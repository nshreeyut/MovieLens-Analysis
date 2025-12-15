import csv
import sys
from pathlib import Path
from collections import defaultdict

# PLACE THIS FILE IN THE ml-32m FOLDER
# ========= CONFIG (EDIT THESE FOR YOUR ANALYSIS) =========

MAX_USERS = 50                 # users 1–50 only
MAX_MOVIES = 400              # cap movie universe at 400 titles
MAX_TAGS_PER_MOVIE = 30       # limit tag rows per movie
MAX_RATINGS_PER_USER = 200    # limit ratings per user
ASCII_ONLY = True            # enforce ASCII-only for titles/genres/tags forf SQL import

# ========================================================


def ensure_file_with_columns(path: Path, required_columns):
    """
    Check that `path` exists and contains all required columns in its header.
    Exit with an error message if something is wrong.
    """
    if not path.exists():
        print(f"ERROR: Expected file '{path.name}' in '{path.parent}', but it was not found.")
        sys.exit(1)

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []

    missing = [c for c in required_columns if c not in columns]
    if missing:
        print(
            f"ERROR: File '{path.name}' is missing required columns: {missing}. "
            f"Found columns: {columns}"
        )
        sys.exit(1)


def sanitize_ascii(s: str) -> str:
    """Return s, optionally stripped to ASCII depending on ASCII_ONLY."""
    if s is None:
        return ""
    if not ASCII_ONLY:
        return s
    return s.encode("ascii", "ignore").decode("ascii")


def build_filtered_ratings(base_dir: Path):
    """
    From ratings.csv, create filtered_ratings.csv with:
      - userId <= MAX_USERS
      - optionally at most MAX_RATINGS_PER_USER ratings per user
    """
    ratings_path = base_dir / "ratings.csv"
    out_path = base_dir / "filtered_ratings.csv"

    required_cols = ["userId", "movieId", "rating", "timestamp"]
    ensure_file_with_columns(ratings_path, required_cols)

    ratings_count = defaultdict(int)  # per-user rating counts

    with ratings_path.open("r", newline="", encoding="utf-8") as f_in, \
         out_path.open("w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=required_cols)
        writer.writeheader()

        kept = 0
        for row in reader:
            user_id = int(row["userId"])

            # stop as soon as we go past MAX_USERS (file is sorted by userId)
            if user_id > MAX_USERS:
                break

            # optionally limit ratings per user
            ratings_count[user_id] += 1
            if MAX_RATINGS_PER_USER is not None and ratings_count[user_id] > MAX_RATINGS_PER_USER:
                continue  # skip extra ratings for this user

            writer.writerow({
                "userId": row["userId"],
                "movieId": row["movieId"],
                "rating": row["rating"],
                "timestamp": row["timestamp"],
            })
            kept += 1

    print(f"Wrote {kept} rows to {out_path.name}")


def load_ids_from_filtered_ratings(base_dir: Path):
    """
    Read filtered_ratings.csv and return:
      - set of unique userIds
      - set of unique movieIds (optionally capped by MAX_MOVIES)
    """
    path = base_dir / "filtered_ratings.csv"
    required_cols = ["userId", "movieId", "rating", "timestamp"]
    ensure_file_with_columns(path, required_cols)

    user_ids = set()
    movie_ids = set()

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_ids.add(int(row["userId"]))
            movie_ids.add(int(row["movieId"]))

    # Optional hard cap on number of movies
    if MAX_MOVIES is not None and len(movie_ids) > MAX_MOVIES:
        # make it reproducible by sorting before slicing
        movie_ids = set(sorted(movie_ids)[:MAX_MOVIES])

    print(f"Found {len(user_ids)} users and {len(movie_ids)} movies in filtered_ratings.csv")
    return user_ids, movie_ids


def build_links_filtered(base_dir: Path, movie_ids):
    """
    From links.csv, create links_filtered.csv containing only rows whose movieId
    appears in `movie_ids`.
    """
    links_path = base_dir / "links.csv"
    out_path = base_dir / "links_filtered.csv"

    required_cols = ["movieId", "imdbId", "tmdbId"]
    ensure_file_with_columns(links_path, required_cols)

    with links_path.open("r", newline="", encoding="utf-8") as f_in, \
         out_path.open("w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=required_cols)
        writer.writeheader()

        kept = 0
        for row in reader:
            movie_id = int(row["movieId"])
            if movie_id in movie_ids:
                writer.writerow(row)
                kept += 1

    print(f"Wrote {kept} rows to {out_path.name}")


def build_tags_filtered(base_dir: Path, allowed_movie_ids):
    """
    From tags.csv, create tags_filtered.csv containing only rows where:
      - movieId is in allowed_movie_ids
    Optionally:
      - cap tags per movie with MAX_TAGS_PER_MOVIE
    """
    tags_path = base_dir / "tags.csv"
    out_path = base_dir / "tags_filtered.csv"

    required_cols = ["userId", "movieId", "tag", "timestamp"]
    ensure_file_with_columns(tags_path, required_cols)

    tags_count = defaultdict(int)  # per-movie tag counts

    with tags_path.open("r", newline="", encoding="utf-8") as f_in, \
         out_path.open("w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=required_cols)
        writer.writeheader()

        kept = 0
        for row in reader:
            movie_id = int(row["movieId"])

            if movie_id not in allowed_movie_ids:
                continue

            # optionally cap number of tags per movie
            tags_count[movie_id] += 1
            if MAX_TAGS_PER_MOVIE is not None and tags_count[movie_id] > MAX_TAGS_PER_MOVIE:
                continue

            writer.writerow({
                "userId": row["userId"],
                "movieId": row["movieId"],
                "tag": sanitize_ascii(row["tag"]),
                "timestamp": row["timestamp"],
            })
            kept += 1

    print(f"Wrote {kept} rows to {out_path.name}")


def build_movies_filtered(base_dir: Path, allowed_movie_ids):
    """
    From movies.csv, create movies_filtered.csv containing only rows whose
    movieId is in allowed_movie_ids.

    Columns kept: movieId,title,genres
    """
    movies_path = base_dir / "movies.csv"
    out_path = base_dir / "movies_filtered.csv"

    required_cols = ["movieId", "title", "genres"]
    ensure_file_with_columns(movies_path, required_cols)

    with movies_path.open("r", newline="", encoding="utf-8") as f_in, \
         out_path.open("w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(
            f_out,
            fieldnames=required_cols,
            quoting=csv.QUOTE_MINIMAL  # auto-quote fields with commas
        )
        writer.writeheader()

        kept = 0
        for row in reader:
            movie_id = int(row["movieId"])
            if movie_id in allowed_movie_ids:
                writer.writerow({
                    "movieId": movie_id,
                    "title": sanitize_ascii(row["title"]),
                    "genres": sanitize_ascii(row["genres"]),
                })
                kept += 1

    print(f"Wrote {kept} rows to {out_path.name}")


def main():
    base_dir = Path(__file__).resolve().parent
    print(f"Working directory detected as: {base_dir}")

    # 1) ratings → filtered_ratings (users up to MAX_USERS)
    build_filtered_ratings(base_dir)

    # 2) get user/movie sets from filtered_ratings (movies may be capped by MAX_MOVIES)
    user_ids, movie_ids = load_ids_from_filtered_ratings(base_dir)

    # 3) links/tags/movies filtered on the same movie set
    build_links_filtered(base_dir, movie_ids)
    build_tags_filtered(base_dir, movie_ids)
    build_movies_filtered(base_dir, movie_ids)

    print("Done.")


if __name__ == "__main__":
    main()
