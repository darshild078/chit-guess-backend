export interface PlayerActivityItemDTO {
  displayName: string;
  isCurrentPlayer: boolean;
  hasSubmitted: boolean;
  connected: boolean;
}

export interface HostActivityItemDTO {
  alias: string;
  aliasId: string;
  hasSubmitted: boolean;
  connected: boolean;
}

export interface HostManagePlayerDTO {
  aliasId: string;
  alias: string;
  connected: boolean;
  hasSubmitted: boolean;
}
