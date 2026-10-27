"""Unit tests for NHL ingestion functions; no network calls are made."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from data_ingestion.api_call_functions import (
    get_season_data,
    get_team_map,
    save_json_from_game,
    save_seasons_data,
)


FIXTURE = Path(__file__).parent / "fixtures" / "play_by_play.json"


class IngestionTests(unittest.TestCase):
    def test_get_team_map_uses_supplied_client(self):
        client = Mock()
        client.teams.teams.return_value = [
            {"abbr": "PIT", "name": "Pittsburgh Penguins"}
        ]

        self.assertEqual(get_team_map(client), {"PIT": "Pittsburgh Penguins"})
        client.teams.teams.assert_called_once_with()

    def test_get_season_data_returns_only_home_regular_season_games(self):
        client = Mock()
        client.schedule.team_season_schedule.return_value = {
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
                    "homeTeam": {"abbrev": "PIT"},
                    "awayTeam": {"abbrev": "CHI"},
                },
                {
                    "id": 9,
                    "gameType": 2,
                    "homeTeam": {"abbrev": "CHI"},
                    "awayTeam": {"abbrev": "PIT"},
                },
            ]
        }

        games = list(get_season_data("20232024", client, ["PIT"]))

        self.assertEqual(games, [{
            "game_id": 7,
            "season": "20232024",
            "away_team_score": 1,
            "home_team_score": 2,
            "home_team_name": "PIT",
            "away_team_name": "CHI",
        }])
        client.schedule.team_season_schedule.assert_called_once_with("PIT", "20232024")

    def test_save_json_preserves_full_api_response(self):
        response = json.loads(FIXTURE.read_text(encoding="utf-8"))
        client = Mock()
        client.game_center.play_by_play.return_value = response

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "nested" / "game.json"
            save_json_from_game(2023020001, output, client)
            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(saved, response)
        self.assertIn("metadata", saved)
        client.game_center.play_by_play.assert_called_once_with(game_id=2023020001)

    @patch("data_ingestion.api_call_functions.pd.DataFrame.to_parquet")
    def test_save_seasons_data_writes_rows_to_explicit_path(self, to_parquet):
        client = Mock()
        with patch(
            "data_ingestion.api_call_functions.get_season_data",
            return_value=iter([{"game_id": 1, "season": "20232024"}]),
        ) as get_games:
            with tempfile.TemporaryDirectory() as temp_dir:
                output = Path(temp_dir) / "nested" / "games.parquet"
                result = save_seasons_data(["20232024"], output, client)

        self.assertEqual(result, output)
        get_games.assert_called_once_with("20232024", client)
        to_parquet.assert_called_once_with(output, index=False)


if __name__ == "__main__":
    unittest.main()
