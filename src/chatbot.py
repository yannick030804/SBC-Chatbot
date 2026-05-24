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
    "recommendation",
    "recomiendame",
    "recomiéndame",
    "recomienda",
    "sugiere",
    "sugerencia",
}

IDLE_STATE = "idle"
COLLECTING_PREFERENCES_STATE = "collecting_preferences"


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


def generate_collect_preferences_response():
    return (
        "I still do not know what you like. Tell me 2 or 3 movies or series you "
        "enjoyed, and I will recommend something based on them."
    )


def generate_collect_preferences_retry_response():
    return (
        "I could not match those titles in my catalog yet. Try with titles from the "
        "database, for example 'Interstellar, Dark and Parasite'."
    )


def get_title_attribute(item, attribute_name, default=None):
    return item.get("if", item).get(attribute_name, default)


def get_conversation_state(db, user_id):
    if db is None or user_id is None:
        return IDLE_STATE

    from models import ConversationState

    state_record = (
        db.query(ConversationState).filter(ConversationState.user_id == user_id).first()
    )

    if state_record is None:
        return IDLE_STATE

    return state_record.state


def set_conversation_state(db, user_id, state):
    if db is None or user_id is None:
        return state

    from models import ConversationState

    state_record = (
        db.query(ConversationState).filter(ConversationState.user_id == user_id).first()
    )

    if state_record is None:
        state_record = ConversationState(user_id=user_id, state=state)
        db.add(state_record)
    else:
        state_record.state = state

    db.commit()
    return state


def get_user_library(db, user_id):
    if db is None or user_id is None:
        return {
            "watched": [],
            "liked": [],
            "favorites": [],
            "disliked": [],
        }

    from models import UserTitle

    records = (
        db.query(UserTitle)
        .filter(UserTitle.user_id == user_id)
        .order_by(UserTitle.title_name.asc())
        .all()
    )

    library = {
        "watched": [],
        "liked": [],
        "favorites": [],
        "disliked": [],
    }

    for record in records:
        if record.watched:
            library["watched"].append(record.title_name)
        if record.liked:
            library["liked"].append(record.title_name)
        if record.favorite:
            library["favorites"].append(record.title_name)
        if record.disliked:
            library["disliked"].append(record.title_name)

    return library


def save_user_title_preferences(
    db,
    user_id,
    titles,
    *,
    watched=False,
    liked=False,
    favorite=False,
    disliked=False,
):
    if db is None or user_id is None or not titles:
        return []

    from models import UserTitle

    updated_titles = []

    for title in titles:
        record = (
            db.query(UserTitle)
            .filter(UserTitle.user_id == user_id, UserTitle.title_name == title)
            .first()
        )

        if record is None:
            record = UserTitle(user_id=user_id, title_name=title)
            db.add(record)

        if watched:
            record.watched = True
        if liked:
            record.liked = True
            record.watched = True
            record.disliked = False
        if favorite:
            record.favorite = True
            record.liked = True
            record.watched = True
            record.disliked = False
        if disliked:
            record.disliked = True
            record.liked = False
            record.favorite = False

        updated_titles.append(title)

    db.commit()
    return updated_titles


def build_user_update_response(updated_titles, label):
    if not updated_titles:
        return ""

    if len(updated_titles) == 1:
        return f"I saved {updated_titles[0]} as {label}."

    title_list = ", ".join(updated_titles[:-1]) + f" and {updated_titles[-1]}"
    return f"I saved {title_list} as {label}."


def has_meaningful_preferences(profile):
    return any(
        [
            profile["type"],
            profile["directors"],
            profile["languages"],
            profile["durations"],
            profile["years"],
            profile["family"] is not None,
            profile["genres_like"],
            profile["mood"],
        ]
    )


def match_items(item, profile, excluded_titles=None):
    score = 0
    conditions = item.get("if", item)
    excluded_titles = excluded_titles or set()

    if item.get("then") in excluded_titles:
        return -1

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


def recommend_best(profile, database, excluded_titles=None):
    matches = []

    for item in database:
        score = match_items(item, profile, excluded_titles=excluded_titles)
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


def recommend_similar_titles(base_title, database, excluded_titles=None):
    item = find_rule_by_title(base_title, database)
    if item is None:
        return []

    excluded_titles = set(excluded_titles or set())
    excluded_titles.add(base_title)

    similar_titles = get_title_attribute(item, "similar_to", [])
    recommendations = []

    for similar_title in similar_titles:
        if similar_title in excluded_titles:
            continue
        similar_item = find_rule_by_title(similar_title, database)
        if similar_item is not None:
            recommendations.append(similar_item)
        if len(recommendations) == 3:
            break

    return recommendations


def recommend_from_seed_titles(seed_titles, database, excluded_titles=None):
    excluded_titles = set(excluded_titles or set())
    ranked_titles = {}

    for title in seed_titles:
        item = find_rule_by_title(title, database)
        if item is None:
            continue

        excluded_titles.add(title)

        for position, similar_title in enumerate(
            get_title_attribute(item, "similar_to", []),
            start=1,
        ):
            if similar_title in excluded_titles:
                continue

            similar_item = find_rule_by_title(similar_title, database)
            if similar_item is None:
                continue

            bonus = max(0, 4 - position)
            ranked_titles[similar_title] = ranked_titles.get(similar_title, 0) + bonus

    if not ranked_titles:
        return []

    recommendations = []
    for title, _score in sorted(
        ranked_titles.items(),
        key=lambda pair: (-pair[1], pair[0]),
    ):
        item = find_rule_by_title(title, database)
        if item is not None:
            recommendations.append(item)
        if len(recommendations) == 3:
            break

    return recommendations


def generate_response(recommendations):
    if not recommendations:
        return "I couldn't find any movie or show that matches all those conditions."

    response = "\nI recommend:\n"

    for item in recommendations:
        response += f"- {item['then']}\n"

    return response


def process_user_message(user_input, db=None, user_id=None):
    cleaned_input = user_input.strip()

    if not cleaned_input:
        return "Write something and I will try to help you."

    if cleaned_input.lower() == "exit":
        return "Goodbye! Enjoy your movies."

    profile = create_profile()
    profile = extract_preferences(cleaned_input, profile, knowledge_base)
    actions = detect_message_actions(cleaned_input)
    intent = classify_intent(cleaned_input, profile)
    user_library = get_user_library(db, user_id)
    conversation_state = get_conversation_state(db, user_id)
    excluded_titles = set(user_library["watched"]) | set(user_library["disliked"])
    known_seed_titles = user_library["favorites"] or user_library["liked"]

    response_parts = []

    if conversation_state == COLLECTING_PREFERENCES_STATE:
        if not profile["liked_titles"]:
            return generate_collect_preferences_retry_response()

        updated_titles = save_user_title_preferences(
            db,
            user_id,
            profile["liked_titles"],
            liked=True,
        )
        set_conversation_state(db, user_id, IDLE_STATE)

        update_message = build_user_update_response(updated_titles, "liked")
        if update_message:
            response_parts.append(update_message)

        recommendations = recommend_from_seed_titles(
            updated_titles,
            knowledge_base,
            excluded_titles=excluded_titles,
        )

        if not recommendations:
            recommendations = recommend_best(
                profile,
                knowledge_base,
                excluded_titles=excluded_titles,
            )

        response_parts.append(generate_response(recommendations).strip())
        return "\n\n".join(part for part in response_parts if part)

    if profile["liked_titles"]:
        titles = profile["liked_titles"]

        if actions["mark_watched"]:
            updated_titles = save_user_title_preferences(
                db,
                user_id,
                titles,
                watched=True,
            )
            update_message = build_user_update_response(updated_titles, "watched")
            if update_message:
                response_parts.append(update_message)

        if actions["mark_liked"] and not actions["mark_favorite"]:
            updated_titles = save_user_title_preferences(
                db,
                user_id,
                titles,
                liked=True,
            )
            update_message = build_user_update_response(updated_titles, "liked")
            if update_message:
                response_parts.append(update_message)

        if actions["mark_favorite"]:
            updated_titles = save_user_title_preferences(
                db,
                user_id,
                titles,
                favorite=True,
            )
            update_message = build_user_update_response(updated_titles, "a favorite")
            if update_message:
                response_parts.append(update_message)

        if actions["mark_disliked"]:
            updated_titles = save_user_title_preferences(
                db,
                user_id,
                titles,
                disliked=True,
                watched=True,
            )
            update_message = build_user_update_response(updated_titles, "disliked")
            if update_message:
                response_parts.append(update_message)

    if intent == "greeting":
        return generate_greeting_response()
    if intent == "info":
        return generate_info_response(profile["liked_titles"][0], knowledge_base)
    if actions["recommend_similar"] and profile["liked_titles"]:
        recommendations = recommend_from_seed_titles(
            profile["liked_titles"],
            knowledge_base,
            excluded_titles=excluded_titles,
        )

        if not recommendations:
            recommendations = recommend_best(
                profile,
                knowledge_base,
                excluded_titles=excluded_titles,
            )

        response_parts.append(generate_response(recommendations).strip())
        return "\n\n".join(part for part in response_parts if part)
    if intent == "recommend":
        if not has_meaningful_preferences(profile) and not known_seed_titles:
            set_conversation_state(db, user_id, COLLECTING_PREFERENCES_STATE)
            return generate_collect_preferences_response()

        if has_meaningful_preferences(profile):
            recommendations = recommend_best(
                profile,
                knowledge_base,
                excluded_titles=excluded_titles,
            )
        else:
            recommendations = recommend_from_seed_titles(
                known_seed_titles,
                knowledge_base,
                excluded_titles=excluded_titles,
            )

        if not recommendations and known_seed_titles:
            recommendations = recommend_from_seed_titles(
                known_seed_titles,
                knowledge_base,
                excluded_titles=excluded_titles,
            )

        response_parts.append(generate_response(recommendations).strip())
        return "\n\n".join(part for part in response_parts if part)

    if response_parts:
        return "\n\n".join(part for part in response_parts if part)

    return generate_unknown_response()


def chatbot():
    print("Movie & Series Chatbot")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Bot: Goodbye! Enjoy your movies")
            break

        print(f"Bot: {process_user_message(user_input)}")


if __name__ == "__main__":
    chatbot()
