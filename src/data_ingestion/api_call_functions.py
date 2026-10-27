import json 
from nhlpy import NHLClient
from pathlib import Path
from functools import partial
from itertools import chain
import pandas as pd
import logging

# setup

DEFAULT_VERBOSE = False

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.Logger("APIFunctionsLogger")
logger.addHandler(console_handler)

USED_PBP_FIELDS = ['id', 'season', 'gameType', 'gameDate', 'venue', 'startTimeUTC', 'awayTeam', 'homeTeam', 'plays', 'rosterSpots', 'regPeriods']
# Part 1. Map Teams to IDs

client = NHLClient()

teams = client.teams.teams() # maps team abbr, name, conference, franchise_id

team_map = {}

for team in teams:
    team_map[team["abbr"]] = team["name"]
    

# Part 2: Fetch all game ids for the last 4 seasons

season_starters = range(2021,2026)

all_seasons = [str(season_starter) + str(season_starter+1)  for season_starter in season_starters]

# get a map for game_id, season, home_team_name, away_team_score, home_team_score

team_abbrs = list(team_map.keys())

def get_season_data(season:str, v:bool = DEFAULT_VERBOSE):
    for team in team_abbrs:
        team_raw_schedule = client.schedule.team_season_schedule(team, season)
        if v:
            logger.info(f"INFO: Downloading games for team {team} in the {season} season")
        games = team_raw_schedule["games"]
        games_data = [{
            "game_id" : game["id"],
            "season" : season,
            "away_team_score": game["awayTeam"].get("score"),
            "home_team_score": game["homeTeam"].get("score"),
            "home_team_name" : game["homeTeam"].get("abbrev"),
            "away_team_name" : game["awayTeam"].get("abbrev")
        } for game in games if game["gameType"] == 2 and game["homeTeam"]["abbrev"] == team]
        
        yield from games_data
            
        
def save_seasons_data(v:bool = DEFAULT_VERBOSE):
    
    games_destination = "data_downloads/games.parquet"
    games_path = Path(games_destination)
    
    if games_path.exists():
        if v:
            logger.info(f"File already exists, skipping")
        return None

    all_games = map(partial(get_season_data, v=v), all_seasons)

    games_df = pd.DataFrame(chain.from_iterable(all_games))

    if v:
        logger.info(games_df.shape)
        logger.info(games_df.head())
        logger.info(f"Are games unique?: {games_df["game_id"].is_unique}")
        logger.info(games_df.groupby("season")["game_id"].nunique())

    # Save so you don't have to hit the API again (needs pyarrow)
    games_df.to_parquet("data_downloads/games.parquet", index=False)
    
    
def save_json_from_game(game_id, v: bool = DEFAULT_VERBOSE):
    file_path = Path(f"data_downloads/pbp_jsons/{game_id}.json")
    if file_path.exists():
        if v:
            logger.info(f"File {file_path} already exists, skipping")
        return None

    file_path.parent.mkdir(parents=True, exist_ok=True)

    pbp = client.game_center.play_by_play(game_id=game_id)
    pbp = {k: val for k, val in pbp.items() if k in USED_PBP_FIELDS}

    if v:
        away = pbp["awayTeam"]["abbrev"]
        home = pbp["homeTeam"]["abbrev"]
        logger.info(f"Saving game {game_id}: {away}@{home} {pbp['gameDate']} in {file_path}")

    with open(file_path, "w") as f:
        json.dump(pbp, f)