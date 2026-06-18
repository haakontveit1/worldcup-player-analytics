"""Helpers for pulling World Cup data from StatsBomb's open data via statsbombpy."""

import pandas as pd
from statsbombpy import sb

WORLD_CUP_COMPETITION_ID = 43


def list_world_cup_seasons() -> pd.DataFrame:
    competitions = sb.competitions()
    return competitions[competitions["competition_id"] == WORLD_CUP_COMPETITION_ID]


def get_matches(season_id: int) -> pd.DataFrame:
    return sb.matches(competition_id=WORLD_CUP_COMPETITION_ID, season_id=season_id)


def get_events(match_id: int) -> pd.DataFrame:
    return sb.events(match_id=match_id)


def get_events_for_season(season_id: int) -> pd.DataFrame:
    matches = get_matches(season_id)
    return pd.concat(
        [get_events(match_id) for match_id in matches["match_id"]],
        ignore_index=True,
    )
