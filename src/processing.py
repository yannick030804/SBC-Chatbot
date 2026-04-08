import re
import string

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

DEFAULT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "to",
    "us",
    "was",
    "we",
    "were",
    "with",
    "you",
    "your",
}


def load_stop_words():
    try:
        return set(stopwords.words("english"))
    except LookupError:
        return set(DEFAULT_STOP_WORDS)


stop_words = load_stop_words()

stop_words.discard("not")
stop_words.discard("no")


def tokenize_text(text):
    try:
        return word_tokenize(text)
    except LookupError:
        return re.findall(r"\b[\w'-]+\b", text.lower())


def preprocess(text):
    text = text.lower()
    tokens = tokenize_text(text)

    cleaned_tokens = []

    for word in tokens:
        if word not in string.punctuation:
            if word not in stop_words:
                cleaned_tokens.append(word)

    return cleaned_tokens


type_key = {
    "movie": ["movie", "movies", "film", "films"],
    "series": ["series", "show", "shows", "tv"],
}

genre_key = {
    "action": ["action"],
    "adventure": ["adventure"],
    "animation": ["animation", "animated"],
    "comedy": ["funny", "comedy", "humour"],
    "crime": ["crime", "criminal"],
    "drama": ["drama"],
    "fantasy": ["fantasy", "magic"],
    "horror": ["horror"],
    "romance": ["romance", "romantic", "love"],
    "sci-fi": ["sci-fi", "science", "space", "future"],
    "thriller": ["thriller", "suspense"],
}

mood_key = {
    "dark": ["dark", "harsh"],
    "emotional": ["emotional"],
    "epic": ["epic"],
    "exciting": ["exciting", "thrilling"],
    "funny": ["funny"],
    "light": ["light", "easy", "relax", "relaxing"],
    "scary": ["scary"],
    "serious": ["serious"],
}

NEGATIONS = ["not", "no"]
LANGUAGE_KEY = {
    "english": "English",
    "korean": "Korean",
    "german": "German",
}
DURATION_KEY = {
    "short": "short",
    "medium": "medium",
    "long": "long",
}
FAMILY_KEY = {
    True: ["family", "kid", "kids", "child", "children"],
    False: ["adult", "adults", "mature"],
}


def create_profile():
    return {
        "type": None,
        "directors": [],
        "languages": [],
        "durations": [],
        "years": [],
        "family": None,
        "genres_like": [],
        "genres_dislike": [],
        "mood": [],
        "liked_titles": [],
    }


def detect_type(text, profile):
    tokens = preprocess(text)

    for word in tokens:
        for content in type_key:
            if word in type_key[content]:
                profile["type"] = content


def detect_languages(text, profile):
    tokens = preprocess(text)

    for word in tokens:
        language = LANGUAGE_KEY.get(word)
        if language and language not in profile["languages"]:
            profile["languages"].append(language)


def detect_durations(text, profile):
    tokens = preprocess(text)

    for word in tokens:
        duration = DURATION_KEY.get(word)
        if duration and duration not in profile["durations"]:
            profile["durations"].append(duration)


def detect_years(text, profile):
    for match in re.findall(r"\b(19\d{2}|20\d{2})\b", text):
        year = int(match)
        if year not in profile["years"]:
            profile["years"].append(year)


def detect_family(text, profile):
    tokens = preprocess(text)

    for word in tokens:
        if word in FAMILY_KEY[True]:
            profile["family"] = True
            return
        if word in FAMILY_KEY[False]:
            profile["family"] = False
            return


# Detect genres
def detect_genres(text, profile):
    tokens = preprocess(text)

    for i in range(len(tokens)):
        word = tokens[i]

        for genre in genre_key:
            if word in genre_key[genre]:
                # Catch simple patterns like "not horror" or "not like horror".
                negation_window = tokens[max(0, i - 2) : i]
                if any(token in NEGATIONS for token in negation_window):
                    if genre not in profile["genres_dislike"]:
                        profile["genres_dislike"].append(genre)
                else:
                    if genre not in profile["genres_like"]:
                        profile["genres_like"].append(genre)


# Detect mood
def detect_mood(text, profile):
    tokens = preprocess(text)

    for word in tokens:
        for mood in mood_key:
            if word in mood_key[mood]:
                if mood not in profile["mood"]:
                    profile["mood"].append(mood)


# Detect mentioned titles
def detect_titles(text, profile, knowledge_base):
    text_lower = text.lower()

    for item in knowledge_base:
        title = item.get("then")
        if not title:
            continue
        title = title.lower()

        if title in text_lower:
            if item["then"] not in profile["liked_titles"]:
                profile["liked_titles"].append(item["then"])


def detect_directors(text, profile, knowledge_base):
    text_lower = text.lower()

    for item in knowledge_base:
        director = item.get("if", {}).get("director")
        if not director:
            continue

        director_parts = [
            part for part in re.split(r"and|,", director.lower()) if part.strip()
        ]
        if director.lower() in text_lower or any(
            part.strip() in text_lower for part in director_parts
        ):
            if director not in profile["directors"]:
                profile["directors"].append(director)


def extract_preferences(user_input, profile, knowledge_base):

    detect_type(user_input, profile)
    detect_directors(user_input, profile, knowledge_base)
    detect_languages(user_input, profile)
    detect_durations(user_input, profile)
    detect_years(user_input, profile)
    detect_family(user_input, profile)
    detect_genres(user_input, profile)
    detect_mood(user_input, profile)
    detect_titles(user_input, profile, knowledge_base)

    return profile
