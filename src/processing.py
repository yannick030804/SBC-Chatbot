import re
import string
from difflib import SequenceMatcher

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
    "dark": ["dark", "darker", "harsh"],
    "emotional": ["emotional"],
    "epic": ["epic"],
    "exciting": ["exciting", "thrilling"],
    "funny": ["funny"],
    "light": ["light", "lighter", "easy", "relax", "relaxing"],
    "scary": ["scary"],
    "serious": ["serious"],
}

NEGATIONS = ["not", "no"]
WATCHED_PATTERNS = [
    "i watched",
    "i have watched",
    "i've watched",
    "i already watched",
    "i saw",
    "i have seen",
    "i've seen",
    "i already saw",
    "i already seen",
    "i just watched",
    "i just saw",
    "already watched",
    "already saw",
    "already seen",
    "just watched",
    "he visto",
    "acabo de ver",
    "vi ",
    "ya vi",
    "ya he visto",
]
LIKED_PATTERNS = [
    "i like",
    "i liked",
    "i love",
    "i loved",
    "i really like",
    "i really liked",
    "i enjoy",
    "i enjoyed",
    "i'm into",
    "i am into",
    "i'm a fan of",
    "i am a fan of",
    "this was good",
    "this is good",
    "me gusto",
    "me gustó",
    "me gustaron",
    "me ha gustado",
    "me gustan",
    "me encanta",
    "me encanto",
    "me encantó",
    "me encantan",
    "me flipa",
    "me flipa",
    "me flipó",
]
DISLIKED_PATTERNS = [
    "i do not like",
    "i don't like",
    "i dislike",
    "i disliked",
    "i hated",
    "i hate",
    "i did not like",
    "i didn't like",
    "i do not enjoy",
    "i don't enjoy",
    "i didn't enjoy",
    "i am not into",
    "i'm not into",
    "i'm not a fan of",
    "i am not a fan of",
    "not a fan of",
    "wasn't good",
    "wasn't great",
    "was not good",
    "was terrible",
    "was awful",
    "was bad",
    "didn't enjoy",
    "did not enjoy",
    "this was bad",
    "this is bad",
    "that was bad",
    "no me gusto",
    "no me gustó",
    "no me ha gustado",
    "no me gustan",
    "no me gusta",
    "no me gustaron",
    "no me encanto",
    "no me encantó",
    "odie",
    "odié",
    "lo odié",
    "la odié",
    "fue mala",
    "fue malo",
    "fue horrible",
    "fue terrible",
    "es mala",
    "es malo",
]
FAVORITE_PATTERNS = [
    "favorite",
    "favourite",
    "one of my favorites",
    "one of my favourites",
    "my favorite",
    "my favourite",
    "top favorite",
    "favorita",
    "favorito",
    "de mis favoritas",
    "de mis favoritos",
    "de mis preferidas",
    "de mis preferidos",
]
SIMILAR_PATTERNS = [
    "similar",
    "like this",
    "like that",
    "something like this",
    "something like that",
    "something similar",
    "anything similar",
    "recommend something like",
    "recommend me something like",
    "recommend me something similar",
    "suggest something like",
    "suggest something similar",
    "parecida",
    "parecido",
    "parecidas",
    "parecidos",
    "algo como",
    "algo similar",
    "algo parecido",
    "recomiendame algo como",
    "recomiéndame algo como",
    "recomiendame algo parecido",
    "recomiéndame algo parecido",
    "sugiereme algo parecido",
    "sugiéreme algo parecido",
]
ANOTHER_RECOMMENDATION_PATTERNS = [
    "another one",
    "another recommendation",
    "another movie",
    "another series",
    "something else",
    "anything else",
    "not that one",
    "not this one",
    "give me another",
    "recommend another",
    "recommend me another",
    "else please",
    "otra",
    "otro",
    "otra recomendacion",
    "otra recomendación",
    "otro titulo",
    "otro título",
    "algo mas",
    "algo más",
    "esa no",
    "ese no",
    "no esa",
    "no ese",
]
GENERIC_TITLE_SKIP_WORDS = {
    "a",
    "an",
    "another",
    "me",
    "no",
    "not",
    "one",
    "that",
    "this",
    "movie",
    "movies",
    "film",
    "films",
    "series",
    "show",
    "shows",
    "tv",
    "something",
    "anything",
    "else",
    "it",
    "please",
    "algo",
    "similar",
    "parecido",
    "parecida",
    "like",
}
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
AMBIGUOUS_TITLE_TOKENS = set(type_key.keys()) | set(genre_key.keys()) | set(mood_key.keys())
GENERIC_PREFERENCE_TOKENS = (
    set(type_key.keys())
    | {token for values in type_key.values() for token in values}
    | set(genre_key.keys())
    | {token for values in genre_key.values() for token in values}
    | set(mood_key.keys())
    | {token for values in mood_key.values() for token in values}
    | set(LANGUAGE_KEY.keys())
    | set(DURATION_KEY.keys())
    | {token for values in FAMILY_KEY.values() for token in values}
)
PERSON_NAME_PATTERN = (
    r"[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){1,3}"
)
PERSON_TRAILING_WORDS = {
    "movie",
    "movies",
    "film",
    "films",
    "series",
    "show",
    "shows",
    "please",
    "long",
    "short",
    "medium",
}


def create_profile():
    return {
        "type": None,
        "directors": [],
        "actors": [],
        "people": [],
        "languages": [],
        "durations": [],
        "years": [],
        "family": None,
        "genres_like": [],
        "genres_dislike": [],
        "mood": [],
        "liked_titles": [],
        "matched_title_candidates": [],
        "unmatched_title_candidates": [],
        "fuzzy_title_matches": {},
        "ambiguous_title_options": [],
        "ambiguous_title_query": None,
    }


def detect_message_actions(text):
    lowered_text = text.lower()

    actions = {
        "mark_watched": any(pattern in lowered_text for pattern in WATCHED_PATTERNS),
        "mark_liked": any(pattern in lowered_text for pattern in LIKED_PATTERNS),
        "mark_disliked": any(pattern in lowered_text for pattern in DISLIKED_PATTERNS),
        "mark_favorite": any(pattern in lowered_text for pattern in FAVORITE_PATTERNS),
        "recommend_similar": any(
            pattern in lowered_text for pattern in SIMILAR_PATTERNS
        ),
        "recommend_another": any(
            pattern in lowered_text
            for pattern in ANOTHER_RECOMMENDATION_PATTERNS
        ),
    }

    if actions["mark_disliked"]:
        actions["mark_liked"] = False

    if actions["mark_favorite"]:
        actions["mark_liked"] = True

    return actions


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


def clean_person_name(name):
    name = name.strip(" .,!?:;")
    parts = name.split()

    while parts and parts[-1].lower() in PERSON_TRAILING_WORDS:
        parts.pop()

    if len(parts) < 2:
        return ""

    return " ".join(parts)


def add_unique_person(profile, field, name):
    cleaned_name = clean_person_name(name)
    if cleaned_name and cleaned_name not in profile[field]:
        profile[field].append(cleaned_name)


def detect_people(text, profile):
    director_patterns = [
        rf"\b(?:directed by|from director|director|by)\s+({PERSON_NAME_PATTERN})",
        rf"\b(?:movie|film|pelicula|película)\s+(?:by|from|de)\s+({PERSON_NAME_PATTERN})",
        rf"\b(?:dirigida por|dirigido por|director de)\s+({PERSON_NAME_PATTERN})",
    ]
    actor_patterns = [
        rf"\b(?:with|starring|featuring|actor|actress|cast)\s+({PERSON_NAME_PATTERN})",
        rf"\b(?:con|protagonizada por|protagonizado por)\s+({PERSON_NAME_PATTERN})",
    ]
    generic_person_patterns = [
        rf"\b({PERSON_NAME_PATTERN})\s+(?:movie|film|series|show)\b",
    ]

    for pattern in director_patterns:
        for match in re.finditer(pattern, text):
            add_unique_person(profile, "directors", match.group(1))

    for pattern in actor_patterns:
        for match in re.finditer(pattern, text):
            add_unique_person(profile, "actors", match.group(1))

    for pattern in generic_person_patterns:
        for match in re.finditer(pattern, text):
            name = clean_person_name(match.group(1))
            if (
                name
                and name not in profile["directors"]
                and name not in profile["actors"]
                and name not in profile["people"]
            ):
                profile["people"].append(name)


def normalize_title_text(text):
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def has_explicit_title_context(text, title):
    escaped_title = re.escape(title.lower())
    title_context_patterns = [
        rf"\b(?:tell me about|give me information about|info about|about)\s+{escaped_title}\b",
        rf"\b(?:i like|i liked|i love|i loved|i enjoy|i enjoyed|i watched|i have seen|i've seen)\s+{escaped_title}\b",
        rf"\b{escaped_title}\s+(?:is|was)\s+(?:one of my favorites|one of my favourites|my favorite|my favourite)\b",
        rf"\b(?:me gusta|me gust[oó]|me gustaron|me encanta|me encant[oó])\s+{escaped_title}\b",
        rf"\b{escaped_title}\s+(?:es|esta|está)\s+(?:entre mis favoritas|entre mis favoritos|de mis favoritas|de mis favoritos|mi favorita|mi favorito)\b",
    ]
    return any(re.search(pattern, text) for pattern in title_context_patterns)


def is_generic_request_fragment(candidate):
    tokens = preprocess(candidate)
    if not tokens:
        return True

    if len(tokens) == 1:
        return (
            tokens[0] in GENERIC_TITLE_SKIP_WORDS
            and tokens[0] not in AMBIGUOUS_TITLE_TOKENS
        )

    if all(token in GENERIC_TITLE_SKIP_WORDS for token in tokens):
        return True

    generic_signal_words = set(type_key.keys()) | set(genre_key.keys()) | set(mood_key.keys())
    if "family" in tokens:
        generic_signal_words.add("family")

    if len(tokens) > 1 and any(token in generic_signal_words for token in tokens):
        return True

    return False


def clean_title_candidate(candidate):
    candidate = candidate.strip()
    candidate = re.sub(
        r"^(i didn't like|i didn't enjoy|i don't like|i did not like|i did not enjoy|"
        r"i do not like|i disliked|i dislike|i hated|i hate|"
        r"i'm not a fan of|i am not a fan of|not a fan of|"
        r"no me gust[oó]|no me ha gustado|no me gustaron|no me encant[oó]|"
        r"odi[eé]|lo odi[eé]|la odi[eé])\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"^(my favorite|my favourite|mi favorita|mi favorito|"
        r"one of my favorites is|one of my favourites is|"
        r"una de mis favoritas es|uno de mis favoritos es|"
        r"me ha gustado mucho|me ha gustado|me gusto mucho|me gustaron|me gust[oó]|"
        r"me encanta|i really like|i really liked|i like|i liked|i loved|i love|"
        r"i enjoy|i enjoyed|i already watched|i have watched|i've watched|i watched|"
        r"i already saw|i already seen|i saw|i have seen|i've seen|i just watched|"
        r"i just saw|he visto|acabo de ver)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"\s+(?:is|was|are|were|es|esta|está|son)?\s*"
        r"(?:one of my favorites|one of my favourites|my favorite|my favourite|"
        r"one of my top favorites|one of my top favourites|"
        r"de mis favoritas|de mis favoritos|entre mis favoritas|entre mis favoritos|"
        r"mi favorita|mi favorito|una de mis favoritas|uno de mis favoritos)\b.*$",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"^(the\s+)?(movie|film|series|show|pelicula|película|serie)(\s+is|\s+was)?\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"^(tell me about|give me information about|give me info about|"
        r"information about|info about|about)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"^(recomiendame|recomiéndame|recommend me|recommend|suggest|sugiere)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    if re.match(
        r"^(algo que sea parecido|algo parecido|something similar|something like)",
        candidate,
        flags=re.IGNORECASE,
    ):
        return ""
    candidate = re.sub(
        r"\s+(recomiendame|recomiéndame|recommend|suggest|algo parecido.*|"
        r"something similar.*)$",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = candidate.strip(" .!?")

    if is_generic_request_fragment(candidate):
        return ""

    return candidate


def extract_title_candidates(text):
    split_pattern = r",|;|\by\b|\band\b"
    raw_candidates = re.split(split_pattern, text, flags=re.IGNORECASE)
    cleaned_candidates = []

    for candidate in raw_candidates:
        cleaned_candidate = clean_title_candidate(candidate)
        if len(cleaned_candidate) >= 3:
            cleaned_candidates.append(cleaned_candidate)

    return cleaned_candidates


def find_best_title_match(candidate, title_index):
    normalized_candidate = normalize_title_text(candidate)
    if not normalized_candidate:
        return None, False

    if normalized_candidate in title_index:
        return title_index[normalized_candidate], False

    best_title = None
    best_score = 0

    for normalized_title, original_title in title_index.items():
        score = SequenceMatcher(None, normalized_candidate, normalized_title).ratio()
        if score > best_score:
            best_score = score
            best_title = original_title

    if best_score >= 0.72:
        return best_title, True

    return None, False


def add_matched_title(profile, title):
    if title not in profile["liked_titles"]:
        profile["liked_titles"].append(title)


GREETING_SKIP_WORDS = {
    "hello", "hi", "hey", "hola", "holi",
    "good morning", "good afternoon", "good evening", "good night",
    "buenos dias", "buenos días", "buenas tardes", "buenas noches",
    "what's up", "whats up", "sup", "yo",
}


AMBIGUOUS_FRANCHISE_TITLES = {
    "batman",
    "star wars",
}


def should_ask_for_title_selection(candidate, similar_results):
    normalized_candidate = normalize_title_text(candidate)

    return (
        normalized_candidate in AMBIGUOUS_FRANCHISE_TITLES
        and len(similar_results) > 1
    )


def sort_title_selection_options(options, candidate):
    normalized_candidate = normalize_title_text(candidate)

    return sorted(
        options,
        key=lambda item: (
            normalize_title_text(item["title"]) != normalized_candidate,
            item.get("media_type") != "movie",
        ),
    )


def detect_titles_tmdb(text, profile, allow_ambiguous_titles=False):
    try:
        from tmdb import search_title
    except ImportError:
        return

    text_lower = text.strip().lower()
    
    if text_lower in GREETING_SKIP_WORDS or len(text_lower) <= 5:
        return
    
    content_type_hint = None
    if "movie" in text_lower or "film" in text_lower or "pelicula" in text_lower or "película" in text_lower:
        content_type_hint = "movie"
    elif "series" in text_lower or "show" in text_lower or "serie" in text_lower:
        content_type_hint = "series"

    cleaned_full_text = clean_title_candidate(text)
    candidates = extract_title_candidates(text)

    if cleaned_full_text and len(cleaned_full_text) >= 3 and len(candidates) <= 1:
        if cleaned_full_text not in candidates:
            candidates.insert(0, cleaned_full_text)

    for candidate in candidates:
        normalized_candidate = normalize_title_text(candidate)
        if not normalized_candidate:
            continue

        candidate_tokens = preprocess(candidate)
        if (
            len(candidate_tokens) == 1
            and candidate_tokens[0] in GENERIC_PREFERENCE_TOKENS
            and not allow_ambiguous_titles
            and not has_explicit_title_context(text_lower, candidate)
        ):
            continue

        people_to_skip = (
            profile["directors"] + profile["actors"] + profile["people"]
        )
        if people_to_skip and any(
            normalize_title_text(person) in normalized_candidate
            for person in people_to_skip
        ):
            continue

        results = search_title(candidate, content_type=content_type_hint)
        if results:
            candidate_lower = candidate.lower().strip()
            normalized_candidate = normalize_title_text(candidate)
            
            similar_results = []
            for r in results[:15]:
                title = r.get("title") or r.get("name") or ""
                title_lower = title.lower()
                
                if candidate_lower in title_lower or title_lower.startswith(candidate_lower.split()[0]):
                    year = ""
                    date = r.get("release_date") or r.get("first_air_date") or ""
                    if date:
                        year = date[:4]
                    similar_results.append({
                        "title": title,
                        "year": year,
                        "id": r.get("id"),
                        "media_type": r.get("media_type", "movie"),
                    })

            if should_ask_for_title_selection(candidate, similar_results):
                profile["ambiguous_title_options"] = sort_title_selection_options(
                    similar_results,
                    candidate,
                )[:6]
                profile["ambiguous_title_query"] = candidate
                return

            exact_result = next(
                (
                    item
                    for item in similar_results
                    if normalize_title_text(item["title"]) == normalized_candidate
                ),
                None,
            )
            if exact_result:
                add_matched_title(profile, exact_result["title"])

                if exact_result["title"] not in profile["matched_title_candidates"]:
                    profile["matched_title_candidates"].append(exact_result["title"])

                continue

            top_title = results[0].get("title") or results[0].get("name") or ""
            if normalize_title_text(top_title) == normalized_candidate:
                add_matched_title(profile, top_title)

                if top_title not in profile["matched_title_candidates"]:
                    profile["matched_title_candidates"].append(top_title)

                continue
            
            if len(similar_results) > 1:
                seen = set()
                unique_results = []
                for r in similar_results:
                    key = (r["title"], r["year"])
                    if key not in seen:
                        seen.add(key)
                        unique_results.append(r)

                profile["ambiguous_title_options"] = sort_title_selection_options(
                    unique_results,
                    candidate,
                )[:6]
                profile["ambiguous_title_query"] = candidate
                return
            
            best_match = results[0]
            matched_title = best_match.get("title") or best_match.get("name")

            if matched_title:
                add_matched_title(profile, matched_title)

                if matched_title not in profile["matched_title_candidates"]:
                    profile["matched_title_candidates"].append(matched_title)

                if candidate.lower() != matched_title.lower():
                    profile["fuzzy_title_matches"][candidate] = matched_title
                
                continue
        else:
            if candidate not in profile["unmatched_title_candidates"]:
                profile["unmatched_title_candidates"].append(candidate)


def extract_preferences(
    user_input,
    profile,
    allow_ambiguous_titles=False,
):

    detect_type(user_input, profile)
    detect_languages(user_input, profile)
    detect_durations(user_input, profile)
    detect_years(user_input, profile)
    detect_family(user_input, profile)
    detect_genres(user_input, profile)
    detect_mood(user_input, profile)
    detect_people(user_input, profile)
    detect_titles_tmdb(
        user_input,
        profile,
        allow_ambiguous_titles=allow_ambiguous_titles,
    )

    return profile
