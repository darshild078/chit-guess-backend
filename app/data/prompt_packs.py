import random
from typing import Dict, List, Any, Optional

# ============================================================================
# SECRET CONFESSIONS PROMPT PACKS
# ============================================================================

CONFESSION_PROMPTS: Dict[str, List[str]] = {
    "general": [
        "What is the most ridiculous lie you told your parents without getting caught?",
        "What is something weird you do when you are completely alone at home?",
        "What is the dumbest way you ever injured yourself?",
        "What is a popular movie, song, or trend that you secretly despise?",
        "What is the worst purchase you've ever made that you immediately regretted?",
        "What is the longest you've ever gone without showering and why?",
        "What is something you pretended to understand for months just to fit in?",
        "What is an irrational childhood fear you secretly still have?",
        "What is the most awkward text or message you sent to the wrong person?",
        "What is something you stole or borrowed and never returned?",
        "What is the worst excuse you gave to get out of hanging out with someone?",
        "What is a weird habit you have that would weird out a stranger?",
        "If you were invisible for 1 hour, what is the first thing you would do?",
        "What is the most embarrassing thing in your web search history right now?",
        "What is the worst haircut or fashion disaster you proudly wore?",
    ],
    "school": [
        "What is the worst trouble you ever got into with a teacher or principal?",
        "What is the craftiest cheat method you ever used during an exam?",
        "What is something ridiculous you faked to skip a day of school?",
        "Who was your most embarrassing childhood celebrity crush?",
        "What did you get detention or sent out of class for?",
        "What was the most awkward presentation or stage moment you had in school?",
        "What rumor did you accidentally start or spread in school?",
    ],
    "embarrassing": [
        "What is an awkward moment from 5+ years ago that still keeps you awake at night?",
        "Have you ever waved back at someone who was actually waving at someone behind you?",
        "What is the most embarrassing thing you did in front of your crush?",
        "What is the worst misunderstanding you've ever had in a public place?",
        "What was your most catastrophic culinary or cooking fail?",
        "What is something you thought was totally normal until someone pointed out it wasn't?",
    ],
    "spicy": [
        "What is the worst date you've ever been on in your life?",
        "What is a petty reason you lost interest in someone you were dating?",
        "Have you ever stalked an ex or crush on social media and accidentally liked a photo?",
        "What is the biggest red flag you completely ignored because they were attractive?",
        "What is a secret gossip secret about a friend you promised never to tell?",
    ],
    "pleasures": [
        "What is a bizarre food combination that you swear tastes amazing?",
        "What is your ultimate guilty pleasure reality TV show or cringe media?",
        "What song do you blast in private that you would never play around friends?",
        "What childish thing do you still do as an adult?",
    ],
}

# ============================================================================
# THE CHAMELEON TOPICS & SECRET WORDS DATABASE
# ============================================================================

CHAMELEON_TOPICS: List[Dict[str, Any]] = [
    {
        "topic": "Fast Food & Dining",
        "words": ["Pizza", "Burger", "French Fries", "Tacos", "Fried Chicken", "Sushi", "Hot Dog", "Ice Cream", "Donuts", "Burrito"],
    },
    {
        "topic": "Superheroes & Villains",
        "words": ["Batman", "Spider-Man", "Superman", "Iron Man", "The Joker", "Thor", "Deadpool", "Wolverine", "Hulk", "Wonder Woman"],
    },
    {
        "topic": "Wild Animals",
        "words": ["Lion", "Elephant", "Penguin", "Giraffe", "Kangaroo", "Cheetah", "Panda", "Shark", "Gorilla", "Zebra"],
    },
    {
        "topic": "Travel & Vacation",
        "words": ["Beach", "Airport", "Passport", "Hotel Resort", "Suitcase", "Cruise Ship", "Mountain", "Souvenir", "Camping", "Sunscreen"],
    },
    {
        "topic": "Movie Genres & Cinema",
        "words": ["Horror", "Comedy", "Popcorn", "Sci-Fi", "Red Carpet", "Director", "Action Hero", "Plot Twist", "Stunt Double", "Hollywood"],
    },
    {
        "topic": "Household Objects",
        "words": ["Toaster", "Refrigerator", "Vacuum", "Blender", "Microwave", "Mirror", "Coffee Maker", "Toothbrush", "Sofa", "Pillow"],
    },
    {
        "topic": "School & College",
        "words": ["Backpack", "Blackboard", "Homework", "Detention", "Cafeteria", "Teacher", "Textbook", "Graduation", "Locker", "Exam"],
    },
    {
        "topic": "Sports & Games",
        "words": ["Football", "Basketball", "Tennis", "Bowling", "Swimming", "Golf", "Skateboarding", "Chess", "Boxing", "Volleyball"],
    },
]

# ============================================================================
# FRIEND ROASTS & FILL-IN-THE-BLANK PROMPTS
# ============================================================================

ROAST_PROMPTS: List[str] = [
    "If {player} was arrested today, the reason on the news would definitely be _______.",
    "If {player} wrote an autobiography, the title on the bestseller list would be _______.",
    "What is {player}'s secret hidden superpower that nobody asked for?",
    "If {player} started a cult, the #1 supreme rule of the cult would be _______.",
    "The real reason {player} would never survive a Zombie Apocalypse is _______.",
    "If {player} entered a reality TV competition, the judges would eliminate them for _______.",
    "What is the weirdest advice {player} would give to someone on a first date?",
    "If {player} was a villain in a movie, their evil master plan would be _______.",
    "What would be the title of {player}'s viral TikTok dance trend?",
    "If {player} won \$10 Million tomorrow, the most ridiculous thing they'd buy first is _______.",
    "What is the ultimate red flag warning label that should be tattooed on {player}?",
    "If {player} was an Uber driver, the 1-star passenger review would say _______.",
]

def get_random_confession_prompt(category: Optional[str] = "general", custom_prompt: Optional[str] = None) -> str:
    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip()
    cat = category if category in CONFESSION_PROMPTS else "general"
    prompts = CONFESSION_PROMPTS.get(cat, CONFESSION_PROMPTS["general"])
    return random.choice(prompts)

def get_random_chameleon_round() -> Dict[str, Any]:
    topic_data = random.choice(CHAMELEON_TOPICS)
    topic = topic_data["topic"]
    words_list = topic_data["words"]
    secret_word = random.choice(words_list)
    # Generate 3 plausible distractors from the same category for the "Last Stand" word guess
    distractors = [w for w in words_list if w != secret_word]
    random.shuffle(distractors)
    choices = [secret_word] + distractors[:3]
    random.shuffle(choices)
    return {
        "topic": topic,
        "secretWord": secret_word,
        "wordChoices": choices,
    }

def get_random_roast_prompt(player_names: List[str], custom_prompt: Optional[str] = None) -> str:
    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip()
    target_player = random.choice(player_names) if player_names else "your friend"
    template = random.choice(ROAST_PROMPTS)
    return template.replace("{player}", target_player)
