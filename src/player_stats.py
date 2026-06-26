"""Derive player-level stats (goals, assists, minutes played, etc.) from
StatsBomb open data, which only ships raw events/lineups - no prebuilt
player season stats like the paid API does.
"""

import pandas as pd

from src.data_loader import get_events


def _parse_clock(value: str | None) -> float | None:
    if value is None:
        return None
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + int(seconds)


def _match_end_seconds(events: pd.DataFrame) -> float:
    """Approximate full-time clock (in seconds) as the latest event timestamp.

    StatsBomb doesn't expose an explicit match-end time, and a player's last
    position interval has `to=None` when they finish the match, so we need
    a stand-in for "when did the match actually end" (accounting for added time).
    """
    last_minute = events["minute"].max()
    last_second = events.loc[events["minute"] == last_minute, "second"].max()
    return last_minute * 60 + last_second


def minutes_played(lineups: dict[str, pd.DataFrame], events: pd.DataFrame) -> pd.DataFrame:
    """One row per player with total minutes played in the match."""
    end_seconds = _match_end_seconds(events)
    rows = []
    for team, df in lineups.items():
        for _, row in df.iterrows():
            total_seconds = 0
            for position in row["positions"]:
                start = _parse_clock(position["from"])
                end = _parse_clock(position["to"]) if position["to"] else end_seconds
                total_seconds += max(end - start, 0)
            rows.append(
                {
                    "player_id": row["player_id"],
                    "player_name": row["player_name"],
                    "team": team,
                    "minutes_played": total_seconds / 60,
                }
            )
    return pd.DataFrame(rows)


def match_event_stats(events: pd.DataFrame) -> pd.DataFrame:
    """One row per player with counting stats from match events.

    Own goals are excluded from `goals` (standard convention - they're
    credited to the scoring team, not the player, in most stat sites).
    """
    by_player = ["player_id", "player", "team"]

    shots = events[events["type"] == "Shot"]
    goals = shots[shots["shot_outcome"] == "Goal"].groupby(by_player).size()
    shot_count = shots.groupby(by_player).size()
    xg = shots.groupby(by_player)["shot_statsbomb_xg"].sum()
    assists = events[events["pass_goal_assist"] == True].groupby(by_player).size()  # noqa: E712
    key_passes = events[events["pass_shot_assist"] == True].groupby(by_player).size()  # noqa: E712
    yellow_cards = events[events["foul_committed_card"] == "Yellow Card"].groupby(by_player).size()
    red_cards = events[
        events["foul_committed_card"].isin(["Red Card", "Second Yellow"])
    ].groupby(by_player).size()

    stats = pd.concat(
        {
            "goals": goals,
            "shots": shot_count,
            "xg": xg,
            "assists": assists,
            "key_passes": key_passes,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
        },
        axis=1,
    ).fillna(0)
    stats = stats.reset_index().rename(columns={"player": "player_name"})
    return stats


def player_match_table(match_id: int, lineups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combined per-player table (minutes + counting stats) for one match."""
    events = get_events(match_id)
    minutes = minutes_played(lineups, events)
    event_stats = match_event_stats(events)

    table = minutes.merge(
        event_stats, on=["player_id", "player_name", "team"], how="left"
    )
    count_cols = ["goals", "shots", "xg", "assists", "key_passes", "yellow_cards", "red_cards"]
    table[count_cols] = table[count_cols].fillna(0)
    table["match_id"] = match_id
    return table


def player_season_table(lineups_by_match: dict[int, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    """Aggregate per-player stats across every match in a competition season.

    `lineups_by_match` must already contain one `sb.lineups()` result per
    match_id in the season (the caller fetches these so progress/errors are
    visible while pulling from the network).
    """
    per_match = [
        player_match_table(match_id, lineups)
        for match_id, lineups in lineups_by_match.items()
    ]
    combined = pd.concat(per_match, ignore_index=True)

    agg = combined.groupby(["player_id", "player_name", "team"]).agg(
        minutes_played=("minutes_played", "sum"),
        matches_played=("match_id", "nunique"),
        goals=("goals", "sum"),
        assists=("assists", "sum"),
        shots=("shots", "sum"),
        xg=("xg", "sum"),
        key_passes=("key_passes", "sum"),
        yellow_cards=("yellow_cards", "sum"),
        red_cards=("red_cards", "sum"),
    ).reset_index()

    agg["goals_per_90"] = agg["goals"] / agg["minutes_played"] * 90
    agg["assists_per_90"] = agg["assists"] / agg["minutes_played"] * 90
    agg["xg_per_90"] = agg["xg"] / agg["minutes_played"] * 90
    return agg
