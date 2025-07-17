# Clash Royale Analyzer

This project provides a simple Streamlit application for fetching and analyzing player data from the official Clash Royale API.

## Setup

1. Obtain an API token from the [Clash Royale Developer Portal](https://developer.clashroyale.com/).
2. Export the token as an environment variable:
   ```bash
   export CLASH_ROYALE_TOKEN="your-token"
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

## Features

- Fetch player information using a tag
- Display trophy count and recent win rate
- View raw battle log on demand

## Additional Setup

To enable YouTube video search, create a [YouTube Data API v3](https://developers.google.com/youtube/v3) key and export it:
```bash
export YOUTUBE_API_KEY="your-youtube-key"
```

## New Feature

- Search YouTube for matchup videos by entering a custom query
