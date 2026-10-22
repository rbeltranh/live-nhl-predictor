import json 
from nhlpy import NHLClient
import argparse

from itertools import chain
import pandas as pd

# setup

DEFAULT_VERBOSE = False

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", default=DEFAULT_VERBOSE)
args = parser.parse_args()

verbose = args.verbose
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

def get_season_data(season:str, v:bool = verbose):
    for team in team_abbrs:
        team_raw_schedule = client.schedule.team_season_schedule(team, season)
        if v:
            print(f"INFO: Downloading games for team {team} in the {season} season")
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
        
        
        
def save_seasons_data(v:bool = verbose):

    all_games = map(get_season_data, all_seasons)

    games_df = pd.DataFrame(chain.from_iterable(all_games))

    if verbose:
        print(games_df.shape)
        print(games_df.head())
        print(games_df["game_id"].is_unique)
        print(games_df.groupby("season")["game_id"].nunique())

    # Save so you don't have to hit the API again (needs pyarrow)
    games_df.to_parquet("data_downloads/games.parquet", index=False)
    

save_seasons_data()