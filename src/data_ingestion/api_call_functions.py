"""NHL API ingestion functions.

Nothing is fetched at import time. Callers provide the client and destinations,
which keeps these functions usable from scripts, tests, and Airflow tasks.
"""

import json
import logging
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)
BACKFILL_SEASON_STARTS = range(2021, 2026)
BACKFILL_SEASONS = tuple(f"{year}{year + 1}" for year in BACKFILL_SEASON_STARTS)


def create_client() -> Any:
    """Create the NHL API client lazily, without network access on import."""
    from nhlpy import NHLClient

    return NHLClient()


def get_team_map(client: Any) -> dict[str, str]:
    """Return team abbreviation to name mapping from the supplied client."""
    return {team["abbr"]: team["name"] for team in client.teams.teams()}


def get_season_data(
    season: str,
    client: Any,
    team_abbrs: Iterable[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield regular-season game summaries for a season.

    The schedule API returns each team's games; selecting games where that team
    is the home team ensures each game is emitted once.
    """
    if team_abbrs is None:
        team_abbrs = get_team_map(client)

    for team in team_abbrs:
        LOGGER.info("Downloading games for team %s in season %s", team, season)
        schedule = client.schedule.team_season_schedule(team, season)
        for game in schedule["games"]:
            if game["gameType"] != 2 or game["homeTeam"]["abbrev"] != team:
                continue
            yield {
                "game_id": game["id"],
                "season": season,
                "away_team_score": game["awayTeam"].get("score"),
                "home_team_score": game["homeTeam"].get("score"),
                "home_team_name": game["homeTeam"].get("abbrev"),
                "away_team_name": game["awayTeam"].get("abbrev"),
            }


def save_seasons_data(
    seasons: Sequence[str],
    output_path: str | Path,
    client: Any,
    *,
    overwrite: bool = False,
) -> Path:
    """Fetch season summaries and save them as a parquet file."""
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        LOGGER.info("File already exists, skipping: %s", destination)
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = (
        row
        for season in seasons
        for row in get_season_data(season, client)
    )
    games_df = pd.DataFrame(rows)
    LOGGER.info("Fetched %d games; unique IDs: %s", len(games_df), games_df["game_id"].is_unique if not games_df.empty else True)
    games_df.to_parquet(destination, index=False)
    return destination


def save_json_from_game(
    game_id: int | str,
    output_path: str | Path,
    client: Any,
    *,
    overwrite: bool = False,
) -> Path:
    """Save the full play-by-play API response for a game as JSON."""
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        LOGGER.info("File already exists, skipping: %s", destination)
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    play_by_play = client.game_center.play_by_play(game_id=game_id)
    with destination.open("w", encoding="utf-8") as output_file:
        json.dump(play_by_play, output_file)

    away = play_by_play.get("awayTeam", {}).get("abbrev", "?")
    home = play_by_play.get("homeTeam", {}).get("abbrev", "?")
    LOGGER.info("Saved game %s (%s@%s) to %s", game_id, away, home, destination)
    return destination
