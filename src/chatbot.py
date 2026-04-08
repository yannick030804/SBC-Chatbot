import json
from pathlib import Path

from processing import *

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "moviesseries.json"

with DATA_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)
    knowledge_base = data.get("rules") or data.get("items") or []

GREETING_WORDS = {
    "hello",
    "hi",
    "hey",
    "hola",
    "good morning",
    "good afternoon",
    "good evening",
}

INFO_KEYWORDS = {
    "info",
    "information",
    "about",
    "details",
    "tell",
    "what",
    "who",
    "when",
}

RECOMMEND_KEYWORDS = {
    "recommend",
    "suggest",
    "watch",
    "looking",
    "want",
    "need",
}


def classify_intent(user_input, profile):
    text = user_input.strip().lower()
    tokens = set(preprocess(user_input))

    if text in GREETING_WORDS or tokens.intersection({"hello", "hi", "hey", "hola"}):
        if (
            len(tokens) <= 3
            and not profile["liked_titles"]
            and not profile["directors"]
            and not profile["languages"]
            and not profile["genres_like"]
            and not profile["mood"]
        ):
            return "greeting"

    if profile["liked_titles"] and (
        "about" in tokens
        or "info" in tokens
        or "information" in tokens
        or "details" in tokens
        or "tell" in tokens
    ):
        return "info"

    if (
        profile["type"]
        or profile["directors"]
        or profile["languages"]
        or profile["durations"]
        or profile["years"]
        or profile["family"] is not None
        or profile["genres_like"]
        or profile["mood"]
        or profile["liked_titles"]
    ):
        return "recommend"

    if tokens.intersection(RECOMMEND_KEYWORDS):
        return "recommend"

    return "unknown"


def find_rule_by_title(title, database):
    title_lower = title.lower()

    for item in database:
        if item.get("then", "").lower() == title_lower:
            return item

    return None


def generate_info_response(title, database):
    item = find_rule_by_title(title, database)
    if item is None:
        return f"I couldn't find information about {title} in my database yet."

    conditions = item.get("if", {})
    genres = ", ".join(conditions.get("genres", [])) or "unknown genres"
    moods = ", ".join(conditions.get("mood", [])) or "unknown mood"
    similar = ", ".join(conditions.get("similar_to", [])) or "no similar titles listed"

    return (
        f"{item['then']} is a {conditions.get('type', 'title')} directed by {conditions.get('director', 'Unknown Director')} "
        f"from {conditions.get('year', 'an unknown year')}. "
        f"It is {genres} with a {moods} tone. "
        f"It runs for {conditions.get('duration_min', 'unknown')} minutes, has a rating of {conditions.get('rating', 'unknown')}, "
        f"and is in {conditions.get('language', 'an unknown language')}. "
        f"Similar titles: {similar}."
    )


def generate_greeting_response():
    return (
        "Hello! I can recommend movies or shows, or give you information about one. "
        "Try something like 'Recommend me a sci-fi movie' or 'Tell me about Inception'."
    )


def generate_unknown_response():
    return (
        "I can help with movie and series recommendations or information about a title. "
        "Try 'Recommend me a comedy series' or 'Give me information about Dark'."
    )


def match_items(item, profile):
    score = 0
    conditions = item.get("if", item)

    if profile["type"] is not None and conditions.get("type") != profile["type"]:
        return -1

    if profile["directors"]:
        director = conditions.get("director", "")
        if director not in profile["directors"]:
            return -1
        score += 2

    if profile["languages"] and conditions.get("language") not in profile["languages"]:
        return -1

    if profile["durations"] and conditions.get("duration") not in profile["durations"]:
        return -1

    if profile["years"] and conditions.get("year") not in profile["years"]:
        return -1

    if profile["family"] is not None and conditions.get("family") != profile["family"]:
        return -1

    for genre in profile["genres_like"]:
        if genre not in conditions.get("genres", []):
            return -1
        score += 1

    for genre in profile["genres_dislike"]:
        if genre in conditions.get("genres", []):
            return -1

    for mood in profile["mood"]:
        if mood not in conditions.get("mood", []):
            return -1
        score += 1

    for liked in profile["liked_titles"]:
        if liked in conditions.get("similar_to", []):
            score += 1

    if profile["type"] is not None and conditions.get("type") == profile["type"]:
        score += 1

    if (
        not profile["directors"]
        and not profile["languages"]
        and not profile["durations"]
        and not profile["years"]
        and profile["family"] is None
        and not profile["genres_like"]
        and not profile["mood"]
        and not profile["liked_titles"]
    ):
        score += conditions.get("rating", 0) / 10

    return score


def get_sort_key(pair):
    score = pair[0]
    item = pair[1]
    conditions = item.get("if", item)
    rating = conditions.get("rating", 0)
    return (score, rating)


def recommend_best(profile, database):
    matches = []

    for item in database:
        score = match_items(item, profile)
        if score >= 0:
            matches.append((score, item))

    if not matches:
        return []

    matches.sort(key=get_sort_key, reverse=True)

    top_score = matches[0][0]

    if profile["directors"]:
        result = []
        for pair in matches[:3]:
            result.append(pair[1])
        return result

    best_items = []
    for score, item in matches:
        if score == top_score and len(best_items) < 3:
            best_items.append(item)

    if best_items:
        return best_items

    result = []
    for pair in matches[:3]:
        result.append(pair[1])
    return result


def generate_response(recommendations):
    if not recommendations:
        return "I couldn't find any movie or show that matches all those conditions."

    response = "\nI recommend:\n"

    for item in recommendations:
        response += f"- {item['then']}\n"

    return response


def chatbot():
    print("Movie & Series Chatbot")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Bot: Goodbye! Enjoy your movies 🍿")
            break

        profile = create_profile()
        profile = extract_preferences(user_input, profile, knowledge_base)
        intent = classify_intent(user_input, profile)

        if intent == "greeting":
            response = generate_greeting_response()
        elif intent == "info":
            response = generate_info_response(
                profile["liked_titles"][0], knowledge_base
            )
        elif intent == "recommend":
            recommendations = recommend_best(profile, knowledge_base)
            response = generate_response(recommendations)
        else:
            response = generate_unknown_response()

        print(f"Bot: {response}")


if __name__ == "__main__":
    chatbot()
