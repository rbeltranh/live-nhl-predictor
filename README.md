# live-nhl-predictor
This repo contains a live nhl probability predictor for matches, with the data pipeline integrated using different technologies. Everything is built to run locally on a Mac/Linux environment.

## Goal 

Predict, after every play, the probability that the home team wins the game. Build two models (logistic regression and a neural network), make them compete on the same data, and serve both models from two inference engines (Python and Rust) and compare them, and run everything on a local data pipeline (Minikube + Airflow).

## Data ingestion

The ingestion code is an installable `src/` package named `data_ingestion`.
From the repository root, install the project in editable mode with `uv sync`,
then run the historical backfill with:

```sh
uv run nhl-ingest --output-dir data_downloads --verbose
```

The same functions can be imported by an Airflow DAG or another Python job:

```python
from data_ingestion import create_client, save_json_from_game, save_seasons_data

client = create_client()
save_seasons_data(("20252026",), "/data/games.parquet", client)
save_json_from_game(2025020001, "/data/pbp_jsons/2025020001.json", client)
```

In Airflow, call these functions from task bodies rather than at DAG module
scope. Imports do not create a client or make NHL API requests. The client,
season/game ID, and output path are explicit inputs, so task execution and tests
can control them.

Raw play-by-play JSON files retain the **full API response**. The extra storage
is inexpensive compared with fetching the games again, and preserving fields
that are not currently used keeps future feature work possible without another
API download.

The one-time backfill covers completed seasons 2021–22 through 2025–26. The
in-progress 2026–27 season is deliberately excluded from the backfill and from
both model training and the final test set. Add it later through a scheduled
Airflow DAG as games become available; keep the final test set limited to its
preselected completed season(s).

Unit tests use mocked NHL clients and the saved response in
`tests/fixtures/play_by_play.json`. Run them with `uv run python -m unittest`.
