# MovieLens Data Cleaning Script

## Description
This Python script filters and cleans the MovieLens dataset for SQL-based analysis.
It generates analysis-ready CSV files from the raw MovieLens data.

## Requirements
- Python 3
- DOWNLOAD - MovieLens dataset folder (`ml-32m` or `ml-latest-small`)

## How to Run

1. Place `data_cleaning.py` inside the MovieLens dataset folder - `ml-32m` 
   Edit the global configuration variables at the top of the script if necessary, then save.

2. Ensure the folder contains the following files:
   - `ratings.csv`
   - `movies.csv`
   - `tags.csv`
   - `links.csv`

3. Run the script from a terminal or any IDE:

   ```bash
   python data_cleaning.py

## Global Configuration Variables
The following variables at the top of `data_cleaning.py` control the scope and size of the dataset used for analysis:

- **MAX_USERS**  
  Limits the analysis to users with `userId ≤ MAX_USERS`, defining the core user sample.
- **MAX_MOVIES**  
  Caps the number of distinct movies included after filtering ratings, keeping the movie universe manageable.
- **MAX_RATINGS_PER_USER**  
  Limits the maximum number of ratings retained per user to prevent highly active users from dominating the dataset.
- **MAX_TAGS_PER_MOVIE**  
  Caps the number of tag records kept per movie to reduce noise and control dataset size.
- **ASCII_ONLY**  
  Enforces ASCII-only text for titles, genres, and tags to ensure SQL-safe CSV imports.

