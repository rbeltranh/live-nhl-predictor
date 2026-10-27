"""Command-line entry point for the historical NHL data backfill."""

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from data_ingestion.api_call_functions import (
    BACKFILL_SEASONS,
    create_client,
    save_json_from_game,
    save_seasons_data,
)

LOGGER = logging.getLogger(__name__)


def download_data(
    client: Any,
    seasons: tuple[str, ...],
    output_dir: str | Path,
) -> None:
    """Download season summaries and each game's full play-by-play response."""
    output_dir = Path(output_dir)
    games_path = output_dir / "games.parquet"
    save_seasons_data(seasons, games_path, client)

    games = pd.read_parquet(games_path)["game_id"]
    LOGGER.info("Downloading play-by-play for %d games", len(games))
    for game_id in games:
        save_json_from_game(
            game_id,
            output_dir / "pbp_jsons" / f"{game_id}.json",
            client,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data_downloads"))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    LOGGER.info("Starting historical backfill for seasons %s", BACKFILL_SEASONS)
    download_data(create_client(), BACKFILL_SEASONS, args.output_dir)


if __name__ == "__main__":
    main()
