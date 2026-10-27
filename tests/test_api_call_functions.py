"""Unit tests for the data ingestion API helpers (without NHL API access)."""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "src" / "data_ingestion" / "tasks"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "play_by_play.json"

# The task modules currently import their sibling config/module by bare name.
# Add their directory as it is when these scripts are run directly.
sys.path.insert(0, str(TASKS_DIR))

# api_call_functions creates its client and requests the team list at import
# time, so replace the client constructor before importing the module.
with patch("nhlpy.NHLClient") as client_factory:
    client_factory.return_value.teams.teams.return_value = [
        {"abbr": "PIT", "name": "Pittsburgh Penguins"}
    ]
    api = importlib.import_module("api_call_functions")


class ApiCallFunctionsTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.team_abbrs_patch = patch.object(api, "team_abbrs", ["PIT"])
        self.team_abbrs_patch.start()
        self.addCleanup(self.team_abbrs_patch.stop)

    def test_get_season_data_returns_home_regular_season_games(self):
        self.client.schedule.team_season_schedule.return_value = {
            "games": [
                {
                    "id": 7,
                    "gameType": 2,
                    "homeTeam": {"abbrev": "PIT", "score": 2},
                    "awayTeam": {"abbrev": "CHI", "score": 1},
                },
                {
                    "id": 8,
                    "gameType": 3,
                    "homeTeam": {"abbrev": "PIT", "score": 3},
                    "awayTeam": {"abbrev": "CHI", "score": 2},
                },
                {
                    "id": 9,
                    "gameType": 2,
                    "homeTeam": {"abbrev": "CHI", "score": 1},
                    "awayTeam": {"abbrev": "PIT", "score": 2},
                },
            ]
        }
        with patch.object(api, "client", self.client):
            games = list(api.get_season_data("20232024"))

        self.assertEqual(
            games,
            [
                {
                    "game_id": 7,
                    "season": "20232024",
                    "away_team_score": 1,
                    "home_team_score": 2,
                    "home_team_name": "PIT",
                    "away_team_name": "CHI",
                }
            ],
        )
        self.client.schedule.team_season_schedule.assert_called_once_with(
            "PIT", "20232024"
        )

    def test_save_seasons_data_fetches_each_backfill_season_and_saves_parquet(self):
        self.client.schedule.team_season_schedule.return_value = {
            "games": [
                {
                    "id": 7,
                    "gameType": 2,
                    "homeTeam": {"abbrev": "PIT", "score": 2},
                    "awayTeam": {"abbrev": "CHI", "score": 1},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "games.parquet"
            with (
                patch.object(api, "client", self.client),
                patch.object(api, "DEFAULT_GAMES_FILE_PATH", str(output_path)),
                patch.object(api.pd.DataFrame, "to_parquet") as to_parquet,
            ):
                api.save_seasons_data()

        self.assertEqual(
            self.client.schedule.team_season_schedule.call_count,
            len(api.all_seasons),
        )
        to_parquet.assert_called_once_with(str(output_path), index=False)

    def test_save_seasons_data_skips_existing_file(self):
        self.client.schedule.team_season_schedule.return_value = {"games": []}
        with (
            patch.object(api, "client", self.client),
            patch.object(api.Path, "exists", return_value=True),
        ):
            result = api.save_seasons_data()

        self.assertIsNone(result)
        self.client.schedule.team_season_schedule.assert_not_called()

    def test_save_json_writes_selected_fields_from_saved_api_response(self):
        response = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.client.game_center.play_by_play.return_value = response

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "pbp_jsons"
            with (
                patch.object(api, "client", self.client),
                patch.object(api, "DEFAULT_PLAY_BY_PLAY_PATH", f"{output_dir}/"),
            ):
                api.save_json_from_game(2023020001)

            saved_path = output_dir / "2023020001.json"
            saved = json.loads(saved_path.read_text(encoding="utf-8"))

        self.assertEqual(set(saved), set(api.USED_PBP_FIELDS))
        self.assertEqual(saved["id"], response["id"])
        self.assertNotIn("metadata", saved)
        self.client.game_center.play_by_play.assert_called_once_with(
            game_id=2023020001
        )

    def test_save_json_skips_existing_file(self):
        self.client.game_center.play_by_play.return_value = {}
        with (
            patch.object(api, "client", self.client),
            patch.object(api.Path, "exists", return_value=True),
        ):
            result = api.save_json_from_game(2023020001)

        self.assertIsNone(result)
        self.client.game_center.play_by_play.assert_not_called()


if __name__ == "__main__":
    unittest.main()
