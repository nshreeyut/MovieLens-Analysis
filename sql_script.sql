CREATE DATABASE IF NOT EXISTS movielens; 
USE movielens;

-- Ensure drops always work even if tables have FK dependencies
SET FOREIGN_KEY_CHECKS = 0;

-- Drop ONLY final tables in right order. 
DROP TABLE IF EXISTS Movies_User_Ratings;
DROP TABLE IF EXISTS Movie_Tags;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Movies;

-- Reenable FOREIGN_KEY_CHECKS
SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- RAW TABLES (CSV SHAPES) - define only if NOT already present
-- (These should be filled with _filtered.csv via the Import Wizard)
-- Run these CREATEs ONLY the first time, or keep them as
-- CREATE TABLE IF NOT EXISTS so they don't overwrite data.
-- =========================================================

CREATE TABLE IF NOT EXISTS movies_raw (
    movieId INT,
    title   VARCHAR(255),
    genres  VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS ratings_raw (
    userId    INT,
    movieId   INT,
    rating    DECIMAL(2,1),
    timestamp BIGINT
);

CREATE TABLE IF NOT EXISTS links_raw (
    movieId INT,
    imdbId  INT,
    tmdbId  INT
);

CREATE TABLE IF NOT EXISTS tags_raw (
    userId    INT,
    movieId   INT,
    tag       VARCHAR(255),
    timestamp BIGINT
);

-- =========================
-- FINAL TABLES
-- =========================

-- ===== STATIC: Movies =====
CREATE TABLE Movies (
  movieId INT NOT NULL,
  movie_title   VARCHAR(255) NOT NULL,
  movie_genres  VARCHAR(255) NOT NULL,
  CONSTRAINT pk_movies PRIMARY KEY (movieId)
) ENGINE=InnoDB;

INSERT INTO Movies (movieId, movie_title, movie_genres)
SELECT DISTINCT movieId, title, genres
FROM movies_raw;

-- ===== STATIC: Users =====
CREATE TABLE Users (
  userId INT NOT NULL,
  CONSTRAINT pk_users PRIMARY KEY (userId)
) ENGINE=InnoDB;

INSERT INTO Users (userId)
SELECT DISTINCT userId FROM ratings_raw
UNION
SELECT DISTINCT userId FROM tags_raw;

-- ===== DYNAMIC: Ratings =====
CREATE TABLE Movies_User_Ratings (
  ratingId INT AUTO_INCREMENT PRIMARY KEY,
  userId  INT NOT NULL,
  movieId INT NOT NULL,
  movie_user_ratings_imdbId INT,
  movie_user_ratings_tmdbId INT,
  movie_user_ratings_number    DECIMAL(2,1) NOT NULL,
  movie_user_ratings_timestamp BIGINT       NOT NULL,
  FOREIGN KEY (movieId) REFERENCES Movies(movieId),
  FOREIGN KEY (userId)  REFERENCES Users(userId)
) ENGINE=InnoDB;

INSERT INTO Movies_User_Ratings (
  userId,
  movieId,
  movie_user_ratings_imdbId,
  movie_user_ratings_tmdbId,
  movie_user_ratings_number,
  movie_user_ratings_timestamp
)
SELECT
    r.userId,
    r.movieId,
    l.imdbId,
    l.tmdbId,
    r.rating,
    r.timestamp
FROM ratings_raw r
JOIN Movies m
  ON r.movieId = m.movieId
LEFT JOIN links_raw l
  ON r.movieId = l.movieId;

-- ===== DYNAMIC: Tags =====
CREATE TABLE Movie_Tags (
  tagId INT AUTO_INCREMENT PRIMARY KEY,
  userId INT NOT NULL,
  movieId INT NOT NULL,
  tag VARCHAR(255) NOT NULL,
  tag_timestamp BIGINT NOT NULL,
  FOREIGN KEY (movieId) REFERENCES Movies(movieId),
  FOREIGN KEY (userId)  REFERENCES Users(userId)
) ENGINE=InnoDB;

INSERT INTO Movie_Tags (userId, movieId, tag, tag_timestamp)
SELECT
    t.userId,
    t.movieId,
    t.tag,
    t.timestamp
FROM tags_raw t
JOIN Movies m
  ON m.movieId = t.movieId;

-- =========================
-- SANITY CHECK (row counts)
-- =========================
SELECT 'Movies' AS table_name, COUNT(*) AS row_count FROM Movies
UNION ALL
SELECT 'Users', COUNT(*) FROM Users
UNION ALL
SELECT 'Movies_User_Ratings', COUNT(*) FROM Movies_User_Ratings
UNION ALL
SELECT 'Movie_Tags', COUNT(*) FROM Movie_Tags;

-- =========================
-- ANALYSIS QUERIES
-- =========================

-- Slide 8 — Genre expansion (movie → multiple rows)
SELECT 
    m.movieId,
    m.movie_title,
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(m.movie_genres, '|', n.n), '|', -1)) AS genre
FROM Movies m
JOIN (
    SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
    UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) n
ON n.n <= 1 + LENGTH(m.movie_genres) - LENGTH(REPLACE(m.movie_genres, '|', ''))
ORDER BY m.movieId, genre;

-- Slide 9 — Average rating by genre
SELECT
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(m.movie_genres, '|', n.n), '|', -1)) AS genre,
    ROUND(AVG(r.movie_user_ratings_number), 2) AS avg_rating,
    COUNT(*) AS rating_count
FROM Movies m
JOIN Movies_User_Ratings r
    ON m.movieId = r.movieId
JOIN (
    SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
    UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) n
ON n.n <= 1 + LENGTH(m.movie_genres) - LENGTH(REPLACE(m.movie_genres, '|', ''))
GROUP BY genre
HAVING COUNT(*) >= 10
ORDER BY avg_rating DESC;

-- Slide 10 — Popularity by rating count (ratings per genre)
SELECT
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(m.movie_genres, '|', n.n), '|', -1)) AS genre,
    COUNT(*) AS total_ratings
FROM Movies m
JOIN Movies_User_Ratings r
    ON m.movieId = r.movieId
JOIN (
    SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
    UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) n
ON n.n <= 1 + LENGTH(m.movie_genres) - LENGTH(REPLACE(m.movie_genres, '|', ''))
GROUP BY genre
HAVING COUNT(*) >= 10
ORDER BY total_ratings DESC;

-- Slide 11 — Top tags by frequency
SELECT
    tag,
    COUNT(*) AS tag_count
FROM Movie_Tags
GROUP BY tag
ORDER BY tag_count DESC
LIMIT 10;
