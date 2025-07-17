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

- Sign up and store your player tag and preferred playstyle
- Fetch player information automatically after login
- Display trophy count and recent win rate
- View raw battle log on demand
- Rate a custom deck (average elixir and tips)
- Detect the deck's playstyle and suggest switching
- Track daily trophies and win rate
- Compare your stats against global quartile benchmarks
- View league benchmarks against players with the same league rank
- Monitor Grand Challenge runs with win tracking and top deck suggestions
  filtered to the 75th percentile or 45% win rate
- Predict opponent hand with a card-counting trainer
- Visualize elixir advantage over time with an interactive slider
- See a daily progress toast with trophy change and win rate
- Optionally mute the toast and enjoy a dark theme optimized for small screens
- Analyze Merge Tactics mode with a tier list of best cards
- Get a Lucky Drop alert when it appears in your battle log
- Watch a pro player for new videos and deck changes

- Enable Qwen Enhance to generate personalized tips
After entering your player tag, you can also paste eight card names separated
by commas to receive a quick deck score and suggestions.

## Additional Setup

Video search now relies on the public [Invidious](https://docs.invidious.io/) API,
so no API key is required.  You can override the default instance by setting
`INVIDIOUS_BASE`:
```bash
export INVIDIOUS_BASE="https://yewtu.be"
```
To enable meta features like trending decks and quartile benchmarks, create a
free RoyaleAPI account and export your token as `ROYALEAPI_TOKEN`:
```bash
export ROYALEAPI_TOKEN="your-royaleapi-token"
```

## Recent Features

- Search YouTube for matchup videos by entering a custom query
- Rate a custom deck directly in the app
- Warn when multiple losses occur in a short time (Tilt Guard)
- Analyze card cycle to ensure you keep spells, win conditions and anti-air in rotation
- Compute an aggression ratio for the first minute of play
- Optional coaching via a locally running Qwen model accessed through Ollama
- Find pro videos for a specific match-up and filter by channel
- Show trending decks from RoyaleAPI (Meta Pulse)
- Suggest deck mutations via Smart Swap and list upgrade priorities
- Recommend an upgrade order by computing ROI for each card
- Track trophy goals and display earned badges
- Monitor temporary event performance with a dedicated Events tab
- Log daily trophy count and win rate in a Progress tab
- Export your progress to CSV or reset the history with one click
- View quartile benchmarks for top players
- Compare your league performance with peers of the same rank
- Follow players or channels and get alerts for new decks or videos
- Toggle Qwen Enhance to use your local model for advice
- Track Grand Challenge runs with win/loss recording and show GC decks
  with at least 45% win rate or in the top quartile
- Display a daily progress toast when you open the app
- Lucky Drop notifier baked into the toast
- New dark theme for better mobile readability
- Store login credentials and playstyle preferences in SQLite
- Analyze Merge Tactics cards in a dedicated tab
- Dockerfile and GitHub Actions CI for easy setup
- Card-counting trainer and elixir heatmap for in-depth replays

## Running Tests

Use:
```bash
python -m unittest discover tests
```

## Packaging & Docker

Install locally using:
```bash
pip install .
```
To build a Docker image and run the app:
```bash
docker build -t crtool .
docker run -p 8501:8501 crtool
```
Continuous integration runs tests via GitHub Actions defined in `.github/workflows/ci.yml`.
