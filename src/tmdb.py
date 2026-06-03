import os
import random
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

TMDB_GENRE_MAP = {
    28: "action",
    12: "adventure",
    16: "animation",
    35: "comedy",
    80: "crime",
    99: "documentary",
    18: "drama",
    10751: "family",
    14: "fantasy",
    36: "history",
    27: "horror",
    10402: "music",
    9648: "mystery",
    10749: "romance",
    878: "sci-fi",
    10770: "tv movie",
    53: "thriller",
    10752: "war",
    37: "western",
    10759: "action & adventure",
    10762: "kids",
    10763: "news",
    10764: "reality",
    10765: "sci-fi & fantasy",
    10766: "soap",
    10767: "talk",
    10768: "war & politics",
}

GENRE_TO_TMDB_ID = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "sci-fi": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37,
}

GENRE_TO_TMDB_ID_TV = {
    "action": 10759,
    "adventure": 10759,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 10765,
    "kids": 10762,
    "mystery": 9648,
    "romance": 10749,
    "sci-fi": 10765,
    "thriller": 9648,
    "war": 10768,
    "western": 37,
}


def tmdb_request(endpoint, params=None):
    if not TMDB_API_KEY:
        return None

    url = f"{TMDB_BASE_URL}{endpoint}"
    default_params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    if params:
        default_params.update(params)

    try:
        response = requests.get(url, params=default_params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def search_movie(query):
    data = tmdb_request("/search/movie", {"query": query})
    if data and data.get("results"):
        return data["results"]
    return []


def search_tv(query):
    data = tmdb_request("/search/tv", {"query": query})
    if data and data.get("results"):
        return data["results"]
    return []


def search_person(query):
    data = tmdb_request("/search/person", {"query": query})
    if data and data.get("results"):
        return data["results"]
    return []


def find_person_ids(names, department=None):
    ids = []

    for name in names or []:
        results = search_person(name)
        if not results:
            continue

        normalized_name = name.lower()
        ranked_results = sorted(
            results,
            key=lambda person: (
                person.get("name", "").lower() != normalized_name,
                department is not None
                and person.get("known_for_department") != department,
                -person.get("popularity", 0),
            ),
        )

        for person in ranked_results:
            if department and person.get("known_for_department") != department:
                continue
            person_id = person.get("id")
            if person_id and person_id not in ids:
                ids.append(person_id)
                break

        if not department and ranked_results:
            person_id = ranked_results[0].get("id")
            if person_id and person_id not in ids:
                ids.append(person_id)

    return ids


def classify_person_ids(names):
    director_ids = []
    actor_ids = []
    person_ids = []

    for name in names or []:
        results = search_person(name)
        if not results:
            continue

        normalized_name = name.lower()
        person = sorted(
            results,
            key=lambda item: (
                item.get("name", "").lower() != normalized_name,
                -item.get("popularity", 0),
            ),
        )[0]
        person_id = person.get("id")
        department = person.get("known_for_department")

        if not person_id:
            continue
        if department == "Directing":
            director_ids.append(person_id)
        elif department == "Acting":
            actor_ids.append(person_id)
        else:
            person_ids.append(person_id)

    return director_ids, actor_ids, person_ids


def search_title(query, content_type=None):
    if content_type == "movie":
        return search_movie(query)
    if content_type == "series":
        return search_tv(query)

    movies = search_movie(query)
    tv_shows = search_tv(query)

    combined = []
    for movie in movies:
        movie["media_type"] = "movie"
        combined.append(movie)
    for show in tv_shows:
        show["media_type"] = "tv"
        combined.append(show)

    combined.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    return combined


def get_movie_details(movie_id):
    data = tmdb_request(f"/movie/{movie_id}")
    if data:
        data["media_type"] = "movie"
    return data


def get_person_movie_credits(person_id):
    data = tmdb_request(f"/person/{person_id}/movie_credits")
    if data:
        return data
    return {}


def get_tv_details(tv_id):
    data = tmdb_request(f"/tv/{tv_id}")
    if data:
        data["media_type"] = "tv"
    return data


def get_title_details(tmdb_id, content_type):
    if content_type == "movie":
        return get_movie_details(tmdb_id)
    if content_type in ("series", "tv"):
        return get_tv_details(tmdb_id)
    return None


def get_collection_details(collection_id):
    return tmdb_request(f"/collection/{collection_id}")


def get_movie_collection_recommendations(movie_id, limit=4):
    details = get_movie_details(movie_id)
    if not details:
        return []

    collection = details.get("belongs_to_collection") or {}
    collection_id = collection.get("id")
    if not collection_id:
        return []

    collection_data = get_collection_details(collection_id)
    if not collection_data or not collection_data.get("parts"):
        return []

    parts = []
    for item in collection_data["parts"]:
        if item.get("id") == movie_id:
            continue
        item["media_type"] = "movie"
        parts.append(item)

    parts.sort(key=lambda item: item.get("release_date") or "")
    return format_tmdb_items(parts[:limit])


def get_similar_movies(movie_id):
    data = tmdb_request(f"/movie/{movie_id}/recommendations")
    if data and data.get("results"):
        for item in data["results"]:
            item["media_type"] = "movie"
        return data["results"]
    return []


def get_similar_tv(tv_id):
    data = tmdb_request(f"/tv/{tv_id}/recommendations")
    if data and data.get("results"):
        for item in data["results"]:
            item["media_type"] = "tv"
        return data["results"]
    return []


def get_similar_titles(tmdb_id, content_type):
    if content_type == "movie":
        return get_similar_movies(tmdb_id)
    if content_type in ("series", "tv"):
        return get_similar_tv(tmdb_id)
    return []


def get_runtime_filters(durations=None):
    durations = durations or []
    runtime_gte = None
    runtime_lte = None

    if "long" in durations:
        runtime_gte = 120
    elif "short" in durations:
        runtime_lte = 90
    elif "medium" in durations:
        runtime_gte = 90
        runtime_lte = 130

    return runtime_gte, runtime_lte


def item_matches_runtime(item, durations=None):
    runtime_gte, runtime_lte = get_runtime_filters(durations)
    if not runtime_gte and not runtime_lte:
        return True

    runtime = item.get("runtime")
    if runtime is None:
        details = get_movie_details(item.get("id"))
        runtime = details.get("runtime") if details else None
        if details:
            item.update(details)

    if runtime is None:
        return False
    if runtime_gte and runtime < runtime_gte:
        return False
    if runtime_lte and runtime > runtime_lte:
        return False
    return True


def item_matches_genres(item, genres=None):
    if not genres:
        return True

    item_genres = set(get_genres_from_ids(item.get("genre_ids", [])))
    return all(genre.lower() in item_genres for genre in genres)


def item_matches_year(item, year=None):
    if not year:
        return True

    release_date = item.get("release_date") or ""
    return release_date.startswith(str(year))


def recommend_movies_by_directors(
    director_ids,
    genres=None,
    year=None,
    durations=None,
    excluded_titles=None,
    limit=4,
):
    excluded_lower = {title.lower() for title in excluded_titles or set()}
    movies = []
    seen_ids = set()

    for director_id in director_ids or []:
        credits = get_person_movie_credits(director_id)
        for item in credits.get("crew", []):
            if item.get("job") != "Director":
                continue
            if item.get("id") in seen_ids:
                continue

            title = item.get("title") or ""
            if title.lower() in excluded_lower:
                continue
            if item.get("vote_count", 0) < 100:
                continue
            if not item_matches_genres(item, genres):
                continue
            if not item_matches_year(item, year):
                continue
            if not item_matches_runtime(item, durations):
                continue

            item["media_type"] = "movie"
            seen_ids.add(item.get("id"))
            movies.append(item)

    movies.sort(
        key=lambda item: (
            item.get("vote_average", 0),
            item.get("vote_count", 0),
            item.get("popularity", 0),
        ),
        reverse=True,
    )
    return format_tmdb_items(movies[:limit])


def discover_movies(
    genres=None,
    year=None,
    sort_by="vote_average.desc",
    page=None,
    director_ids=None,
    actor_ids=None,
    person_ids=None,
    durations=None,
):
    has_specific_filters = any([director_ids, actor_ids, person_ids, durations, year])
    if page is None:
        page = 1 if has_specific_filters else random.randint(1, 5)
    
    params = {
        "sort_by": sort_by,
        "page": page,
        "vote_count.gte": 100,
    }

    if genres:
        genre_ids = []
        for genre in genres:
            genre_id = GENRE_TO_TMDB_ID.get(genre.lower())
            if genre_id:
                genre_ids.append(str(genre_id))
        if genre_ids:
            params["with_genres"] = ",".join(genre_ids)

    if year:
        params["primary_release_year"] = year

    if director_ids:
        params["with_crew"] = ",".join(str(person_id) for person_id in director_ids)

    if actor_ids:
        params["with_cast"] = ",".join(str(person_id) for person_id in actor_ids)

    if person_ids:
        params["with_people"] = ",".join(str(person_id) for person_id in person_ids)

    runtime_gte, runtime_lte = get_runtime_filters(durations)
    if runtime_gte:
        params["with_runtime.gte"] = runtime_gte
    if runtime_lte:
        params["with_runtime.lte"] = runtime_lte

    data = tmdb_request("/discover/movie", params)
    if data and data.get("results"):
        results = data["results"]
        if has_specific_filters:
            results.sort(
                key=lambda item: (
                    item.get("vote_average", 0),
                    item.get("vote_count", 0),
                    item.get("popularity", 0),
                ),
                reverse=True,
            )
        else:
            random.shuffle(results)
        for item in results:
            item["media_type"] = "movie"
        return results
    return []


def discover_tv(
    genres=None,
    year=None,
    sort_by="vote_average.desc",
    page=None,
    actor_ids=None,
    person_ids=None,
    durations=None,
):
    has_specific_filters = any([actor_ids, person_ids, durations, year])
    if page is None:
        page = 1 if has_specific_filters else random.randint(1, 5)
    
    params = {
        "sort_by": sort_by,
        "page": page,
        "vote_count.gte": 50,
    }

    if genres:
        genre_ids = []
        for genre in genres:
            genre_id = GENRE_TO_TMDB_ID_TV.get(genre.lower())
            if genre_id:
                genre_ids.append(str(genre_id))
        if genre_ids:
            params["with_genres"] = ",".join(genre_ids)

    if year:
        params["first_air_date_year"] = year

    if actor_ids:
        params["with_people"] = ",".join(str(person_id) for person_id in actor_ids)

    if person_ids:
        params["with_people"] = ",".join(str(person_id) for person_id in person_ids)

    runtime_gte, runtime_lte = get_runtime_filters(durations)
    if runtime_gte:
        params["with_runtime.gte"] = runtime_gte
    if runtime_lte:
        params["with_runtime.lte"] = runtime_lte

    data = tmdb_request("/discover/tv", params)
    if data and data.get("results"):
        results = data["results"]
        if has_specific_filters:
            results.sort(
                key=lambda item: (
                    item.get("vote_average", 0),
                    item.get("vote_count", 0),
                    item.get("popularity", 0),
                ),
                reverse=True,
            )
        else:
            random.shuffle(results)
        for item in results:
            item["media_type"] = "tv"
        return results
    return []


def discover_titles(
    content_type=None,
    genres=None,
    year=None,
    director_ids=None,
    actor_ids=None,
    person_ids=None,
    durations=None,
):
    if content_type == "movie":
        return discover_movies(
            genres=genres,
            year=year,
            director_ids=director_ids,
            actor_ids=actor_ids,
            person_ids=person_ids,
            durations=durations,
        )
    if content_type == "series":
        return discover_tv(
            genres=genres,
            year=year,
            actor_ids=actor_ids,
            person_ids=person_ids,
            durations=durations,
        )

    movies = discover_movies(
        genres=genres,
        year=year,
        director_ids=director_ids,
        actor_ids=actor_ids,
        person_ids=person_ids,
        durations=durations,
    )
    tv_shows = discover_tv(
        genres=genres,
        year=year,
        actor_ids=actor_ids,
        person_ids=person_ids,
        durations=durations,
    )

    combined = movies + tv_shows
    combined.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    return combined


def get_genres_from_ids(genre_ids):
    genres = []
    for genre_id in genre_ids:
        genre_name = TMDB_GENRE_MAP.get(genre_id)
        if genre_name:
            genres.append(genre_name)
    return genres


def format_tmdb_item(item):
    media_type = item.get("media_type", "movie")
    is_movie = media_type == "movie"

    title = item.get("title") if is_movie else item.get("name")
    release_date = item.get("release_date") if is_movie else item.get("first_air_date")
    year = release_date[:4] if release_date else None

    genres = []
    if item.get("genres"):
        genres = [g["name"].lower() for g in item["genres"]]
    elif item.get("genre_ids"):
        genres = get_genres_from_ids(item["genre_ids"])

    poster_url = None
    if item.get("poster_path"):
        poster_url = f"{TMDB_IMAGE_BASE_URL}{item['poster_path']}"

    return {
        "id": item.get("id"),
        "title": title,
        "type": "movie" if is_movie else "series",
        "year": year,
        "overview": item.get("overview"),
        "rating": item.get("vote_average"),
        "genres": genres,
        "poster_url": poster_url,
        "popularity": item.get("popularity"),
        "runtime": item.get("runtime"),
        "language": item.get("original_language"),
    }


def format_tmdb_items(items):
    return [format_tmdb_item(item) for item in items]


def find_title_by_name(query):
    results = search_title(query)
    if not results:
        return None

    best_match = results[0]
    media_type = best_match.get("media_type", "movie")

    if media_type == "movie":
        details = get_movie_details(best_match["id"])
    else:
        details = get_tv_details(best_match["id"])

    if details:
        return format_tmdb_item(details)

    return format_tmdb_item(best_match)


def recommend_by_title(title_name, content_type=None, limit=4):
    results = search_title(title_name, content_type=content_type)
    if not results:
        return []

    base_item = results[0]
    tmdb_id = base_item["id"]
    media_type = base_item.get("media_type", "movie")

    if media_type == "movie":
        collection_recommendations = get_movie_collection_recommendations(
            tmdb_id,
            limit=limit,
        )
        if collection_recommendations:
            return collection_recommendations

    similar = get_similar_titles(tmdb_id, media_type)
    if not similar:
        return []

    formatted = format_tmdb_items(similar[:limit])
    return formatted


def recommend_by_tmdb_id(tmdb_id, media_type="movie", limit=4):
    if not tmdb_id:
        return []

    if media_type == "movie":
        collection_recommendations = get_movie_collection_recommendations(
            tmdb_id,
            limit=limit,
        )
        if collection_recommendations:
            return collection_recommendations

    similar = get_similar_titles(tmdb_id, media_type)
    if not similar:
        return []

    return format_tmdb_items(similar[:limit])


def recommend_by_preferences(
    content_type=None,
    genres=None,
    year=None,
    directors=None,
    actors=None,
    people=None,
    durations=None,
    excluded_titles=None,
    limit=4,
):
    excluded_titles = excluded_titles or set()
    excluded_lower = {t.lower() for t in excluded_titles}
    director_ids = find_person_ids(directors, department="Directing")
    actor_ids = find_person_ids(actors, department="Acting")
    generic_director_ids, generic_actor_ids, generic_person_ids = classify_person_ids(
        people
    )
    director_ids.extend(
        person_id for person_id in generic_director_ids if person_id not in director_ids
    )
    actor_ids.extend(
        person_id for person_id in generic_actor_ids if person_id not in actor_ids
    )
    person_ids = generic_person_ids

    if director_ids and content_type is None:
        content_type = "movie"

    if director_ids and content_type in (None, "movie"):
        director_results = recommend_movies_by_directors(
            director_ids,
            genres=genres,
            year=year,
            durations=durations,
            excluded_titles=excluded_titles,
            limit=limit,
        )
        if director_results:
            return director_results

    results = discover_titles(
        content_type=content_type,
        genres=genres,
        year=year,
        director_ids=director_ids,
        actor_ids=actor_ids,
        person_ids=person_ids,
        durations=durations,
    )

    filtered = []
    for item in results:
        title = item.get("title") or item.get("name")
        if title and title.lower() not in excluded_lower:
            filtered.append(item)

    formatted = format_tmdb_items(filtered[:limit])
    return formatted


def get_title_info(title_name):
    item = find_title_by_name(title_name)
    if not item:
        return None
    return item
