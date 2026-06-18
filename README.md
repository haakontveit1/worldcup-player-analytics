# World Cup Player Analytics

Analysis of FIFA World Cup data using [StatsBomb's open data](https://github.com/statsbomb/open-data), focused on player-level performance and estimating the probability of in-match events (goals, shots, key passes, etc.).

## Goals

- Pull event and match data for World Cup competitions via [statsbombpy](https://github.com/statsbomb/statsbombpy).
- Build player-level features (shots, xG, passes, duels, etc.).
- Estimate odds/probabilities for events of interest (e.g. probability a player scores, probability of a shot becoming a goal given location and situation).
- Visualize findings (shot maps, pass networks, event distributions).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Project structure

- `notebooks/` — exploratory analysis and visualizations (Jupyter)
- `src/` — reusable data loading and feature engineering code
- `data/` — cached/derived data (gitignored; raw StatsBomb data is fetched on demand via statsbombpy)

## Data source

[StatsBomb open data](https://github.com/statsbomb/open-data) is free for public, non-commercial use under their [license](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf). Includes detailed event data for several men's and women's World Cups.
