from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.core.exceptions import AppException
from app.core.logging import logger

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": exc.error_code,
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        primary_message = "Please check your inputs and try again."

        for err in exc.errors():
            loc = [str(x) for x in err.get("loc", []) if x not in ("body", "query", "path")]
            field_name = loc[-1] if loc else "field"
            msg = err.get("msg", "Invalid input value.")

            if "at least" in msg or "min_length" in msg:
                primary_message = f"{field_name.replace('_', ' ').capitalize()} is too short."
            elif "at most" in msg or "max_length" in msg:
                primary_message = f"{field_name.replace('_', ' ').capitalize()} is too long."
            elif "missing" in msg:
                primary_message = f"{field_name.replace('_', ' ').capitalize()} is required."
            else:
                primary_message = msg
            break

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": primary_message,
                "data": None,
                "error_code": "VALIDATION_ERROR",
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(f"Database integrity conflict: {exc}")
        orig_msg = str(getattr(exc, "orig", exc)).lower()

        if "participant_roomid_displayname_key" in orig_msg or "unique constraint" in orig_msg:
            message = "A player with this name is already in the room. Please choose a different name."
            code = "DUPLICATE_NAME"
        elif "room_code_key" in orig_msg:
            message = "A room with this code already exists. Please try again."
            code = "ROOM_CODE_COLLISION"
        elif "chitmessage_roundid_senderid_key" in orig_msg:
            message = "You have already submitted a secret word for this round."
            code = "ALREADY_SUBMITTED"
        else:
            message = "A conflict occurred with existing room data. Please refresh and try again."
            code = "CONFLICT"

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": message,
                "data": None,
                "error_code": code,
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(OperationalError)
    async def operational_exception_handler(request: Request, exc: OperationalError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Database is temporarily reconnecting. Please retry in a few seconds.",
                "data": None,
                "error_code": "DATABASE_UNAVAILABLE",
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"SQLAlchemy error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Unable to complete database operation. Please try again.",
                "data": None,
                "error_code": "DATABASE_ERROR",
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred while processing your request. Please try again.",
                "data": None,
                "error_code": "INTERNAL_ERROR",
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )
