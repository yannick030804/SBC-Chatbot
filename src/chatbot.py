import json

from processing import (
    create_profile,
    preprocess,
    extract_preferences,
    detect_message_actions,
)
from tmdb import (
    recommend_by_title,
    recommend_by_tmdb_id,
    recommend_by_preferences,
    get_title_info,
)

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
AWAITING_TYPE_STATE = "awaiting_type_preference"
AWAITING_MOOD_MOVIE_STATE = "awaiting_mood_preference_movie"
AWAITING_MOOD_SERIES_STATE = "awaiting_mood_preference_series"
AWAITING_TITLE_SELECTION_STATE = "awaiting_title_selection"
FLEXIBLE_REPLY_WORDS = {
    "anything",
    "whatever",
    "either",
    "any",
    "lo que sea",
    "me da igual",
    "cualquiera",
    "cualquier cosa",
}
PENDING_CONVERSATION_STATES = {
    COLLECTING_PREFERENCES_STATE,
    AWAITING_TYPE_STATE,
    AWAITING_MOOD_MOVIE_STATE,
    AWAITING_MOOD_SERIES_STATE,
    AWAITING_TITLE_SELECTION_STATE,
}


def is_short_greeting(text):
    normalized_text = text.strip().lower()
    tokens = set(preprocess(text))

    return len(tokens) <= 3 and (
        normalized_text in GREETING_WORDS
        or bool(tokens.intersection({"hello", "hi", "hey", "hola"}))
    )


def classify_intent(user_input, profile):
    tokens = set(preprocess(user_input))

    if is_short_greeting(user_input):
        if (
            len(tokens) <= 3
            and not profile["liked_titles"]
            and not profile["directors"]
            and not profile["actors"]
            and not profile["people"]
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
        or profile["actors"]
        or profile["people"]
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


def generate_info_response(title):
    item = get_title_info(title)
    if item is None:
        return f"I couldn't find information about '{title}' in my database."

    genres = ", ".join(item.get("genres", [])) or "unknown genres"
    year = item.get("year") or "an unknown year"
    rating = item.get("rating")
    rating_str = f"{rating:.1f}/10" if rating else "unknown"
    runtime = item.get("runtime")
    runtime_str = f"{runtime} minutes" if runtime else "unknown duration"
    overview = item.get("overview") or "No description available."

    return (
        f"{item['title']} ({year}) is a {item['type']}. "
        f"Genres: {genres}. Rating: {rating_str}. Runtime: {runtime_str}.\n\n"
        f"{overview}"
    )


def generate_greeting_response():
    return (
        "Hello! I can recommend movies or shows, and I can also talk about specific "
        "titles. Try something like 'Recommend me a sci-fi movie' or 'Tell me about Inception'."
    )


def generate_unknown_response():
    return (
        "I can help with recommendations or information about a title. Try something "
        "like 'Recommend me a comedy series' or 'Tell me about Dark'."
    )


def generate_collect_preferences_response():
    return (
        "I do not know your tastes yet. Tell me 2 or 3 movies or series you enjoyed, "
        "and I will recommend something based on them."
    )


def generate_collect_preferences_retry_response():
    return (
        "I could not match those titles in my catalog yet. Try a few titles from the "
        "database, for example 'Interstellar, Dark and Parasite'."
    )


def generate_collect_preferences_reminder_response():
    return (
        "I still need a couple of titles you liked before I can personalize a recommendation. "
        "Try something like 'Interstellar, Dark and Parasite'."
    )


def generate_type_question_response():
    return "Sure. Do you want a movie or a series?"


def generate_type_retry_response():
    return "I can work with either movies or series. Which one do you want right now?"


def generate_mood_question_response(content_type):
    return f"Got it. Do you want a darker {content_type} or something lighter?"


def generate_mood_retry_response():
    return "Do you want something darker or lighter?"


def generate_title_selection_question(options, query):
    lines = [f"I found several titles matching '{query}'. Which one do you mean?"]
    for i, opt in enumerate(options, 1):
        year_str = f" ({opt['year']})" if opt.get("year") else ""
        lines.append(f"{i}. {opt['title']}{year_str}")
    return "\n".join(lines)


def format_selected_title(option):
    title = option.get("title", "")
    year = option.get("year")

    if year and f"({year})" not in title:
        return f"{title} ({year})"

    return title


def parse_title_selection(user_input, options):
    text = user_input.strip()
    
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(options):
            return options[index]
    
    text_lower = text.lower()
    for opt in options:
        if opt["title"].lower() == text_lower:
            return opt
        if opt.get("year") and opt["year"] in text:
            title_lower = opt["title"].lower()
            if any(word in text_lower for word in title_lower.split()[:3]):
                return opt
    
    return None


def generate_personalization_hint():
    return (
        "If you want, tell me a couple of movies or series you liked and I can "
        "make the next recommendations more personal."
    )


def generate_guided_greeting_response(conversation_state, profile):
    if conversation_state == COLLECTING_PREFERENCES_STATE:
        return (
            "Hello! Before I personalize anything, tell me 2 or 3 movies or series "
            "you liked."
        )

    if conversation_state == AWAITING_TYPE_STATE:
        return "Hello! Do you want a movie or a series?"

    if conversation_state == AWAITING_MOOD_MOVIE_STATE:
        return "Hello! Do you want a darker movie or something lighter?"

    if conversation_state == AWAITING_MOOD_SERIES_STATE:
        return "Hello! Do you want a darker series or something lighter?"

    if conversation_state == AWAITING_TITLE_SELECTION_STATE:
        return "Hello! Which title did you mean? Reply with the number or the title name."

    if profile["type"] == "movie" and profile["mood"]:
        return f"Hello! Do you want a darker movie or something lighter?"

    if profile["type"] == "series" and profile["mood"]:
        return f"Hello! Do you want a darker series or something lighter?"

    return generate_greeting_response()


def format_title_list(titles):
    if not titles:
        return ""
    if len(titles) == 1:
        return titles[0]
    return ", ".join(titles[:-1]) + f" and {titles[-1]}"


def build_title_detection_feedback(profile):
    unmatched_titles = profile.get("unmatched_title_candidates", [])
    if unmatched_titles:
        return "I couldn't find: " + format_title_list(unmatched_titles) + "."
    return ""


def get_title_attribute(item, attribute_name, default=None):
    return item.get(attribute_name, default)


def build_profile_from_state(state, profile):
    if state == AWAITING_MOOD_MOVIE_STATE and profile["type"] is None:
        profile["type"] = "movie"
    if state == AWAITING_MOOD_SERIES_STATE and profile["type"] is None:
        profile["type"] = "series"
    return profile


def merge_profile_with_context(profile, context):
    if not context:
        return profile

    if profile["type"] is None and context.get("type"):
        profile["type"] = context["type"]

    if profile["family"] is None and context.get("family") is not None:
        profile["family"] = context["family"]

    for field in [
        "directors",
        "actors",
        "people",
        "languages",
        "durations",
        "years",
        "genres_like",
        "genres_dislike",
        "mood",
        "liked_titles",
    ]:
        for value in context.get(field, []):
            if value not in profile[field]:
                profile[field].append(value)

    return profile


def build_context_from_profile(profile):
    return {
        "type": profile["type"],
        "directors": profile["directors"],
        "actors": profile["actors"],
        "people": profile["people"],
        "languages": profile["languages"],
        "durations": profile["durations"],
        "years": profile["years"],
        "family": profile["family"],
        "genres_like": profile["genres_like"],
        "genres_dislike": profile["genres_dislike"],
        "mood": profile["mood"],
        "liked_titles": profile["liked_titles"],
    }


def merge_context_updates(context, **updates):
    merged_context = dict(context or {})

    for key, value in updates.items():
        if value is None:
            merged_context.pop(key, None)
        else:
            merged_context[key] = value

    return merged_context


def should_override_guided_state(intent, profile, actions):
    return (
        intent == "info"
        or actions.get("mark_watched")
        or actions.get("mark_liked")
        or actions.get("mark_disliked")
        or actions.get("mark_favorite")
        or bool(profile["liked_titles"])
        or bool(profile["directors"])
        or bool(profile["actors"])
        or bool(profile["people"])
    )


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


def get_conversation_context(db, user_id):
    if db is None or user_id is None:
        return {}

    from models import ConversationState

    state_record = (
        db.query(ConversationState).filter(ConversationState.user_id == user_id).first()
    )

    if state_record is None or not state_record.context:
        return {}

    try:
        return json.loads(state_record.context)
    except json.JSONDecodeError:
        return {}


def set_conversation_state(db, user_id, state, context=None):
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

    state_record.context = json.dumps(context or {})

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

    title_list = format_title_list(updated_titles)

    if label == "watched":
        if len(updated_titles) == 1:
            return f"Got it, I'll keep {title_list} as something you've already watched."
        return f"Got it, I'll keep {title_list} as titles you've already watched."

    if label == "liked":
        if len(updated_titles) == 1:
            return f"Nice, I'll keep {title_list} in mind as something you liked."
        return f"Nice, I'll keep {title_list} in mind as titles you liked."

    if label == "liked and watched":
        if len(updated_titles) == 1:
            return (
                f"Got it, I'll remember {title_list} as something you liked and "
                "already watched."
            )
        return (
            f"Got it, I'll remember {title_list} as titles you liked and already "
            "watched."
        )

    if label == "a favorite":
        if len(updated_titles) == 1:
            return f"Great, I'll remember {title_list} as one of your favorites."
        return f"Great, I'll remember {title_list} as some of your favorites."

    if label == "disliked":
        if len(updated_titles) == 1:
            return f"Understood, I'll avoid recommending things too close to {title_list}."
        return f"Understood, I'll avoid recommending things too close to {title_list}."

    if len(updated_titles) == 1:
        return f"I saved {title_list} as {label}."
    return f"I saved {title_list} as {label}."


def has_meaningful_preferences(profile):
    return any(
        [
            profile["type"],
            profile["directors"],
            profile["actors"],
            profile["people"],
            profile["languages"],
            profile["durations"],
            profile["years"],
            profile["family"] is not None,
            profile["genres_like"],
            profile["mood"],
        ]
    )


def is_open_recommendation_request(profile):
    return (
        profile["type"] is None
        and not profile["mood"]
        and not profile["genres_like"]
        and not profile["directors"]
        and not profile["actors"]
        and not profile["people"]
        and not profile["languages"]
        and not profile["durations"]
        and not profile["years"]
        and profile["family"] is None
        and not profile["liked_titles"]
    )


def is_flexible_reply(text):
    return text.strip().lower() in FLEXIBLE_REPLY_WORDS


def get_candidate_types(profile, excluded_titles=None):
    return {"movie", "series"}


def recommend_best(profile, excluded_titles=None):
    excluded_titles = excluded_titles or set()
    year = profile["years"][0] if profile["years"] else None

    results = recommend_by_preferences(
        content_type=profile["type"],
        genres=profile["genres_like"] if profile["genres_like"] else None,
        year=year,
        directors=profile["directors"],
        actors=profile["actors"],
        people=profile["people"],
        durations=profile["durations"],
        excluded_titles=excluded_titles,
        limit=4,
    )

    return results


def recommend_from_seed_titles(seed_titles, excluded_titles=None, content_type=None):
    excluded_titles = set(excluded_titles or set())
    seed_recommendations = []

    for title in seed_titles:
        similar = recommend_by_title(title, content_type=content_type, limit=6)
        filtered_recommendations = []

        for item in similar:
            item_title = item.get("title", "")
            item_type = item.get("type", "")
            
            if content_type and item_type != content_type:
                continue

            filtered_recommendations.append(item)

        seed_recommendations.append(filtered_recommendations)

    excluded_lower = {title.lower() for title in excluded_titles}
    seen_titles = set(excluded_lower)
    recommendations = []
    max_results = max((len(items) for items in seed_recommendations), default=0)

    # Interleave results so multiple liked titles can influence the final answer.
    for index in range(max_results):
        for items in seed_recommendations:
            if index >= len(items):
                continue

            item = items[index]
            item_title = item.get("title", "")
            normalized_title = item_title.lower()

            if normalized_title and normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                recommendations.append(item)

            if len(recommendations) == 4:
                return recommendations

    return recommendations


def recommend_from_selected_title(
    seed_titles,
    selected_title,
    excluded_titles=None,
    content_type=None,
):
    excluded_titles = set(excluded_titles or set())
    seed_recommendations = []

    for title in seed_titles:
        seed_recommendations.append(
            [
                item
                for item in recommend_by_title(
                    title,
                    content_type=content_type,
                    limit=6,
                )
                if not content_type or item.get("type") == content_type
            ]
        )

    selected_recommendations = recommend_by_tmdb_id(
        selected_title.get("id"),
        selected_title.get("media_type", "movie"),
        limit=6,
    )
    if content_type:
        selected_recommendations = [
            item
            for item in selected_recommendations
            if item.get("type") == content_type
        ]

    seed_recommendations.append(selected_recommendations)

    excluded_lower = {title.lower() for title in excluded_titles}
    seen_titles = set(excluded_lower)
    recommendations = []
    max_results = max((len(items) for items in seed_recommendations), default=0)

    for index in range(max_results):
        for items in seed_recommendations:
            if index >= len(items):
                continue

            item = items[index]
            item_title = item.get("title", "")
            normalized_title = item_title.lower()

            if normalized_title and normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                recommendations.append(item)

            if len(recommendations) == 4:
                return recommendations

    return recommendations


def get_recommendation_titles(recommendations):
    return [item.get("title", "") for item in recommendations]


def remember_recommendations(db, user_id, context, recommendations, profile):
    shown_recommendations = get_recommendation_titles(recommendations[:4])
    recent_recommendations = list(context.get("last_recommendations", []))

    for title in shown_recommendations:
        if title not in recent_recommendations:
            recent_recommendations.append(title)

    set_conversation_state(
        db,
        user_id,
        IDLE_STATE,
        context=merge_context_updates(
            context,
            last_recommendations=recent_recommendations[-10:],
            last_recommendation_profile=build_context_from_profile(profile),
        ),
    )


def build_recommendation_response(
    db,
    user_id,
    context,
    recommendations,
    profile,
    intro=None,
):
    remember_recommendations(db, user_id, context, recommendations, profile)
    return generate_explained_response(recommendations, profile, intro=intro)


def explain_recommendation_match(item, profile, intro=None):
    reasons = []
    intro_text = (intro or "").lower()

    item_genres = item.get("genres", [])
    matching_genres = [
        genre for genre in profile["genres_like"] if genre in item_genres
    ]
    if matching_genres:
        reasons.append(f"It leans into {format_title_list(matching_genres)}.")

    if item.get("rating") and item["rating"] >= 7.5:
        reasons.append(f"It has a strong rating of {item['rating']:.1f}/10.")

    if profile["liked_titles"]:
        reasons.append(
            f"It has a similar vibe to {format_title_list(profile['liked_titles'][:2])}."
        )

    return reasons[:2]


def generate_reason_sentence(reasons):
    if not reasons:
        return ""

    return " " + " ".join(reasons)


def generate_recommendation_text(title, item, profile, intro=None):
    reasons = explain_recommendation_match(item, profile, intro=intro)
    return f"You could try {title}.{generate_reason_sentence(reasons)}"


def generate_response(recommendations, intro=None):
    if not recommendations:
        return "I couldn't find anything that matches what you're asking for."

    titles = [item.get("title", "Unknown") for item in recommendations]

    if intro:
        if len(titles) == 1:
            return f"{intro} you could try {titles[0]}."
        if len(titles) == 2:
            return f"{intro} you could try {titles[0]} or {titles[1]}."
        return (
            f"{intro} you could try {titles[0]}, {titles[1]}, or {titles[2]}."
        )

    if len(titles) == 1:
        return f"You could try {titles[0]}."

    if len(titles) == 2:
        return f"You could try {titles[0]} or {titles[1]}."

    return f"You could try {titles[0]}, {titles[1]}, or {titles[2]}."


def generate_explained_response(recommendations, profile, intro=None):
    if not recommendations:
        return "I couldn't find anything that matches what you're asking for."

    if len(recommendations) == 1:
        item = recommendations[0]
        title = item.get("title", "Unknown")
        reasons = explain_recommendation_match(item, profile, intro=intro)
        reason_text = generate_reason_sentence(reasons)

        if intro:
            return f"{intro} you could try {title}.{reason_text}"
        return f"You could try {title}.{reason_text}"

    response_parts = []

    if intro:
        response_parts.append(f"{intro} here are some options:\n")
    else:
        response_parts.append("Here are some options:\n")

    for item in recommendations[:4]:
        title = item.get("title", "Unknown")
        year = item.get("year", "")
        rating = item.get("rating")

        title_line = f"- {title}"
        if year:
            title_line += f" ({year})"
        if rating:
            title_line += f" - {rating:.1f}/10"

        response_parts.append(title_line)

    return "\n".join(response_parts)


def build_recommendation_intro(profile, actions, updated_titles=None):
    updated_titles = updated_titles or []

    if actions.get("mark_watched") and updated_titles:
        return (
            f"Since you've already watched {format_title_list(updated_titles)},"
        )

    if actions.get("mark_liked") and updated_titles:
        return f"Since you liked {format_title_list(updated_titles)},"

    if actions.get("recommend_similar") and profile["liked_titles"]:
        return f"If you want something along the lines of {format_title_list(profile['liked_titles'])},"

    if profile["type"] == "movie":
        return "If you're in the mood for a movie,"

    if profile["type"] == "series":
        return "If you're in the mood for a series,"

    return ""


def should_add_personalization_hint(user_library, profile, updated_titles=None):
    updated_titles = updated_titles or []
    if user_library["liked"] or user_library["favorites"]:
        return False
    if updated_titles:
        return False
    if profile["liked_titles"]:
        return False
    return True


def has_saved_taste_data(user_library):
    return bool(user_library["liked"] or user_library["favorites"])


def should_reuse_last_recommendation_context(actions, profile):
    if not actions.get("recommend_another"):
        return False

    return (
        profile["type"] is None
        and not profile["directors"]
        and not profile["actors"]
        and not profile["people"]
        and not profile["languages"]
        and not profile["durations"]
        and not profile["years"]
        and profile["family"] is None
        and not profile["genres_like"]
        and not profile["mood"]
        and not profile["liked_titles"]
    )


def has_new_action_while_selecting(text):
    actions = detect_message_actions(text)
    tokens = set(preprocess(text))

    return (
        bool(tokens.intersection(RECOMMEND_KEYWORDS | INFO_KEYWORDS))
        or actions.get("mark_watched")
        or actions.get("mark_liked")
        or actions.get("mark_disliked")
        or actions.get("mark_favorite")
        or actions.get("recommend_similar")
        or actions.get("recommend_another")
    )


def get_pending_title_action(text, actions):
    tokens = set(preprocess(text))

    if tokens.intersection(INFO_KEYWORDS):
        return "info"
    if actions.get("mark_favorite"):
        return "favorite"
    if actions.get("mark_disliked"):
        return "disliked"
    if actions.get("mark_watched") and actions.get("mark_liked"):
        return "liked_watched"
    if actions.get("mark_watched"):
        return "watched"
    if actions.get("recommend_similar"):
        return "liked"
    if actions.get("mark_liked"):
        return "liked"

    return "mentioned"


def should_save_pending_titles_as_liked(conversation_state, pending_action):
    return conversation_state == COLLECTING_PREFERENCES_STATE or pending_action in {
        "liked",
        "liked_watched",
        "favorite",
    }


def build_partial_title_selection_intro(saved_titles, pending_action):
    if not saved_titles:
        return ""

    if pending_action == "favorite":
        return build_user_update_response(saved_titles, "a favorite")

    if pending_action == "liked_watched":
        return build_user_update_response(saved_titles, "liked and watched")

    return build_user_update_response(saved_titles, "liked")


def build_relaxed_profile_for_another(profile):
    relaxed_profile = create_profile()
    relaxed_profile["type"] = profile["type"]

    for title in profile["liked_titles"]:
        if title not in relaxed_profile["liked_titles"]:
            relaxed_profile["liked_titles"].append(title)

    return relaxed_profile


def build_seed_profile(seed_titles, content_type=None):
    profile = create_profile()
    profile["type"] = content_type

    for title in seed_titles:
        if title not in profile["liked_titles"]:
            profile["liked_titles"].append(title)

    return profile


def process_user_message(user_input, db=None, user_id=None):
    cleaned_input = user_input.strip()

    if not cleaned_input:
        return "Write something and I will try to help you."

    if cleaned_input.lower() == "exit":
        return "Goodbye! Enjoy your movies."

    user_library = get_user_library(db, user_id)
    conversation_state = get_conversation_state(db, user_id)
    conversation_context = get_conversation_context(db, user_id)
    
    if conversation_state == AWAITING_TITLE_SELECTION_STATE:
        pending_options = conversation_context.get("pending_title_options", [])
        pending_action = conversation_context.get("pending_action", "liked")
        
        if pending_options:
            if is_short_greeting(cleaned_input):
                return generate_guided_greeting_response(conversation_state, create_profile())

            selected = parse_title_selection(cleaned_input, pending_options)
            if selected:
                set_conversation_state(db, user_id, IDLE_STATE)
                title = format_selected_title(selected)
                pending_seed_titles = conversation_context.get("pending_seed_titles", [])
                
                if pending_action == "liked":
                    save_user_title_preferences(db, user_id, [title], liked=True)
                    seed_titles = pending_seed_titles + [title]
                    seed_profile = build_seed_profile(seed_titles)
                    recommendations = recommend_from_selected_title(
                        pending_seed_titles,
                        selected,
                    )
                    if pending_seed_titles:
                        response = f"Got it! I'll also keep {title} in mind as something you liked."
                    else:
                        response = f"Got it! I'll keep {title} in mind as something you liked."
                    if recommendations:
                        response += "\n\n" + build_recommendation_response(
                            db, user_id, {}, recommendations,
                            seed_profile, intro="Based on those titles,"
                        )
                    return response
                elif pending_action == "liked_watched":
                    save_user_title_preferences(db, user_id, [title], liked=True, watched=True)
                    seed_titles = pending_seed_titles + [title]
                    seed_profile = build_seed_profile(seed_titles)
                    recommendations = recommend_from_selected_title(
                        pending_seed_titles,
                        selected,
                    )
                    if pending_seed_titles:
                        response = f"Got it! I'll also remember {title} as something you liked and already watched."
                    else:
                        response = f"Got it! I'll remember {title} as something you liked and already watched."
                    if recommendations:
                        response += "\n\n" + build_recommendation_response(
                            db, user_id, {}, recommendations,
                            seed_profile, intro="Based on those titles,"
                        )
                    return response
                elif pending_action == "watched":
                    save_user_title_preferences(db, user_id, [title], watched=True)
                    return f"Got it, I'll keep {title} as something you've already watched."
                elif pending_action == "favorite":
                    save_user_title_preferences(db, user_id, [title], favorite=True)
                    seed_titles = pending_seed_titles + [title]
                    seed_profile = build_seed_profile(seed_titles)
                    recommendations = recommend_from_selected_title(
                        pending_seed_titles,
                        selected,
                    )
                    response = f"Great! I'll keep {title} as one of your favorites."
                    if recommendations:
                        response += "\n\n" + build_recommendation_response(
                            db, user_id, {}, recommendations,
                            seed_profile, intro="Based on your favorite,"
                        )
                    return response
                elif pending_action == "disliked":
                    save_user_title_preferences(db, user_id, [title], disliked=True)
                    return f"Understood, I'll avoid recommending things too close to {title}."
                elif pending_action == "info":
                    return generate_info_response(title)
                else:
                    return f"Got it, you mentioned {title}."
            else:
                if has_new_action_while_selecting(cleaned_input):
                    set_conversation_state(db, user_id, IDLE_STATE)
                    conversation_state = IDLE_STATE
                    conversation_context = {}
                else:
                    return "I didn't understand your selection. Please reply with the number (1, 2, 3...) or the title name."
    
    profile = create_profile()
    profile = extract_preferences(
        cleaned_input,
        profile,
        allow_ambiguous_titles=conversation_state == COLLECTING_PREFERENCES_STATE,
    )
    
    if profile.get("ambiguous_title_options"):
        options = profile["ambiguous_title_options"]
        query = profile["ambiguous_title_query"]
        actions = detect_message_actions(cleaned_input)
        pending_action = get_pending_title_action(cleaned_input, actions)
        if conversation_state == COLLECTING_PREFERENCES_STATE and pending_action == "mentioned":
            pending_action = "liked"
        pending_seed_titles = list(profile["liked_titles"])
        intro_message = ""

        if (
            pending_seed_titles
            and should_save_pending_titles_as_liked(conversation_state, pending_action)
        ):
            save_user_title_preferences(
                db,
                user_id,
                pending_seed_titles,
                liked=True,
                watched=pending_action == "liked_watched",
                favorite=pending_action == "favorite",
            )
            intro_message = build_partial_title_selection_intro(
                pending_seed_titles,
                pending_action,
            )
        
        set_conversation_state(
            db, user_id, AWAITING_TITLE_SELECTION_STATE,
            context={
                "pending_title_options": options,
                "pending_action": pending_action,
                "pending_seed_titles": pending_seed_titles,
            }
        )
        selection_question = generate_title_selection_question(options, query)
        if intro_message:
            return intro_message + "\n\n" + selection_question
        return selection_question
    
    actions = detect_message_actions(cleaned_input)
    current_message_titles = list(profile["liked_titles"])
    if conversation_state in PENDING_CONVERSATION_STATES:
        profile = merge_profile_with_context(profile, conversation_context)
    if should_reuse_last_recommendation_context(actions, profile):
        profile = merge_profile_with_context(
            profile,
            conversation_context.get("last_recommendation_profile", {}),
        )
    profile = build_profile_from_state(conversation_state, profile)
    intent = classify_intent(cleaned_input, profile)
    excluded_titles = set(user_library["watched"]) | set(user_library["disliked"])
    if actions["recommend_another"] and not current_message_titles:
        excluded_titles.update(conversation_context.get("last_recommendations", []))
        intent = "recommend"
    known_seed_titles = user_library["favorites"] or user_library["liked"]

    response_parts = []
    title_feedback = build_title_detection_feedback(profile)

    if conversation_state in PENDING_CONVERSATION_STATES and is_short_greeting(
        cleaned_input
    ):
        return generate_guided_greeting_response(conversation_state, profile)

    if conversation_state == AWAITING_TYPE_STATE:
        if should_override_guided_state(intent, profile, actions):
            set_conversation_state(db, user_id, IDLE_STATE)
            conversation_state = IDLE_STATE
        elif is_flexible_reply(cleaned_input):
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )
            if not recommendations and known_seed_titles:
                recommendations = recommend_from_seed_titles(
                    known_seed_titles,
                    excluded_titles=excluded_titles,
                    content_type=profile["type"],
                )
            response = build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro="Got it, I'll keep it broad,",
            )
            if should_add_personalization_hint(user_library, profile):
                response += "\n\n" + generate_personalization_hint()
            return response
        elif profile["type"] is None:
            return generate_type_retry_response()

    if conversation_state in {AWAITING_MOOD_MOVIE_STATE, AWAITING_MOOD_SERIES_STATE}:
        if should_override_guided_state(intent, profile, actions):
            set_conversation_state(db, user_id, IDLE_STATE)
            conversation_state = IDLE_STATE

    if conversation_state == AWAITING_TYPE_STATE:
        if profile["type"] is None:
            return generate_type_retry_response()

        if (
            profile["mood"]
            or profile["genres_like"]
            or profile["directors"]
            or profile["actors"]
            or profile["people"]
            or profile["languages"]
            or profile["durations"]
        ):
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )
            if not recommendations and known_seed_titles:
                recommendations = recommend_from_seed_titles(
                    known_seed_titles,
                    excluded_titles=excluded_titles,
                    content_type=profile["type"],
                )
            response = build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro=build_recommendation_intro(profile, actions),
            )
            if should_add_personalization_hint(user_library, profile):
                response += "\n\n" + generate_personalization_hint()
            return response

        next_state = (
            AWAITING_MOOD_MOVIE_STATE
            if profile["type"] == "movie"
            else AWAITING_MOOD_SERIES_STATE
        )
        set_conversation_state(
            db,
            user_id,
            next_state,
            context=build_context_from_profile(profile),
        )
        return generate_mood_question_response(profile["type"])

    if conversation_state in {AWAITING_MOOD_MOVIE_STATE, AWAITING_MOOD_SERIES_STATE}:
        if is_flexible_reply(cleaned_input):
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )
            if not recommendations and known_seed_titles:
                recommendations = recommend_from_seed_titles(
                    known_seed_titles,
                    excluded_titles=excluded_titles,
                    content_type=profile["type"],
                )
            response = build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro=build_recommendation_intro(profile, actions),
            )
            if should_add_personalization_hint(user_library, profile):
                response += "\n\n" + generate_personalization_hint()
            return response

        if not profile["mood"]:
            return generate_mood_retry_response()

        recommendations = recommend_best(
            profile,
            excluded_titles=excluded_titles,
        )

        if not recommendations and known_seed_titles:
            recommendations = recommend_from_seed_titles(
                known_seed_titles,
                excluded_titles=excluded_titles,
                content_type=profile["type"],
            )

        response = build_recommendation_response(
            db,
            user_id,
            conversation_context,
            recommendations,
            profile,
            intro=(
                f"Since you're in the mood for a {profile['mood'][0]} "
                f"{profile['type']},"
            ),
        )
        if should_add_personalization_hint(user_library, profile):
            response += "\n\n" + generate_personalization_hint()
        return response

    if conversation_state == COLLECTING_PREFERENCES_STATE:
        if not profile["liked_titles"]:
            if intent == "recommend":
                return generate_collect_preferences_reminder_response()
            if title_feedback:
                return (
                    title_feedback + " " + generate_collect_preferences_retry_response()
                )
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
        if title_feedback:
            response_parts.append(title_feedback)

        recommendations = recommend_from_seed_titles(
            updated_titles,
            excluded_titles=excluded_titles,
            content_type=profile["type"],
        )

        if not recommendations:
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )

        response_parts.append(
            build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro=f"Based on those titles,",
            ).strip()
        )
        return "\n\n".join(part for part in response_parts if part)

    recent_update_titles = []

    if profile["liked_titles"]:
        titles = profile["liked_titles"]

        if (
            actions["mark_watched"]
            and actions["mark_liked"]
            and not actions["mark_favorite"]
            and not actions["mark_disliked"]
        ):
            updated_titles = save_user_title_preferences(
                db,
                user_id,
                titles,
                watched=True,
                liked=True,
            )
            update_message = build_user_update_response(
                updated_titles,
                "liked and watched",
            )
            if update_message:
                response_parts.append(update_message)
            recent_update_titles = updated_titles
            excluded_titles.update(updated_titles)
            actions["mark_watched"] = False
            actions["mark_liked"] = False

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
            recent_update_titles = updated_titles
            excluded_titles.update(updated_titles)

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
            recent_update_titles = updated_titles
            excluded_titles.update(updated_titles)

            recommendations = recommend_from_seed_titles(
                updated_titles,
                excluded_titles=excluded_titles,
                content_type=profile["type"],
            )
            if recommendations:
                response_parts.append(
                    build_recommendation_response(
                        db,
                        user_id,
                        conversation_context,
                        recommendations,
                        profile,
                        intro="Since you liked that,",
                    ).strip()
                )
                return "\n\n".join(part for part in response_parts if part)

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
            recent_update_titles = updated_titles
            excluded_titles.update(updated_titles)

            recommendations = recommend_from_seed_titles(
                updated_titles,
                excluded_titles=excluded_titles,
                content_type=profile["type"],
            )
            if recommendations:
                response_parts.append(
                    build_recommendation_response(
                        db,
                        user_id,
                        conversation_context,
                        recommendations,
                        profile,
                        intro="Based on your favorite,",
                    ).strip()
                )
                return "\n\n".join(part for part in response_parts if part)

        if actions["mark_disliked"]:
            was_previously_liked = any(
                t in user_library["liked"] or t in user_library["favorites"]
                for t in titles
            )
            
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
            
            if was_previously_liked:
                response_parts.append(
                    "I've also removed it from your liked titles."
                )
            
            recent_update_titles = updated_titles
            excluded_titles.update(updated_titles)
            
            known_seed_titles = user_library["favorites"] or user_library["liked"]
            if known_seed_titles:
                recommendations = recommend_from_seed_titles(
                    [t for t in known_seed_titles if t not in excluded_titles],
                    excluded_titles=excluded_titles,
                    content_type=profile["type"],
                )
                if recommendations:
                    response_parts.append(
                        build_recommendation_response(
                            db,
                            user_id,
                            conversation_context,
                            recommendations,
                            profile,
                            intro="Maybe you'd prefer something like this instead:",
                        ).strip()
                    )
            
            return "\n\n".join(part for part in response_parts if part)

    if intent == "greeting":
        return generate_greeting_response()
    if intent == "info":
        return generate_info_response(profile["liked_titles"][0])
    if actions["recommend_similar"] and profile["liked_titles"]:
        if title_feedback:
            response_parts.append(title_feedback)
        recommendations = recommend_from_seed_titles(
            profile["liked_titles"],
            excluded_titles=excluded_titles,
            content_type=profile["type"],
        )

        if not recommendations:
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )

        response_parts.append(
            build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro=build_recommendation_intro(
                    profile,
                    actions,
                    updated_titles=recent_update_titles or profile["liked_titles"],
                ),
            ).strip()
        )
        if should_add_personalization_hint(
            user_library,
            profile,
            updated_titles=recent_update_titles,
        ):
            response_parts.append(generate_personalization_hint())
        return "\n\n".join(part for part in response_parts if part)
    if intent == "recommend":
        if is_open_recommendation_request(profile):
            if not has_saved_taste_data(user_library):
                set_conversation_state(db, user_id, COLLECTING_PREFERENCES_STATE)
                return generate_collect_preferences_response()

            set_conversation_state(
                db,
                user_id,
                AWAITING_TYPE_STATE,
                context=build_context_from_profile(profile),
            )
            return generate_type_question_response()

        if profile["type"] is None and not profile["liked_titles"]:
            candidate_types = get_candidate_types(
                profile,
                excluded_titles=excluded_titles,
            )
            if len(candidate_types) > 1:
                set_conversation_state(
                    db,
                    user_id,
                    AWAITING_TYPE_STATE,
                    context=build_context_from_profile(profile),
                )
                return generate_type_question_response()

        if title_feedback:
            response_parts.append(title_feedback)

        recommendations = []
        
        if profile["liked_titles"]:
            recommendations = recommend_from_seed_titles(
                profile["liked_titles"],
                excluded_titles=excluded_titles,
                content_type=profile["type"],
            )
        elif known_seed_titles:
            recommendations = recommend_from_seed_titles(
                known_seed_titles,
                excluded_titles=excluded_titles,
                content_type=profile["type"],
            )
        
        if not recommendations and has_meaningful_preferences(profile):
            recommendations = recommend_best(
                profile,
                excluded_titles=excluded_titles,
            )

        if not recommendations and actions["recommend_another"]:
            recommendations = recommend_best(
                build_relaxed_profile_for_another(profile),
                excluded_titles=excluded_titles,
            )

        response_parts.append(
            build_recommendation_response(
                db,
                user_id,
                conversation_context,
                recommendations,
                profile,
                intro=build_recommendation_intro(
                    profile,
                    actions,
                    updated_titles=recent_update_titles,
                ),
            ).strip()
        )
        return "\n\n".join(part for part in response_parts if part)

    if response_parts:
        if title_feedback and title_feedback not in response_parts:
            response_parts.append(title_feedback)
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
