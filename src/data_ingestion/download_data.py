import argparse
import pandas as pd
import logging
from api_call_functions import *



console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.Logger("DownloaderLogger")
logger.addHandler(console_handler)

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", default=DEFAULT_VERBOSE)
args = parser.parse_args()

verbose = args.verbose


# Saves season games data
logger.info(f"Downloading data with verbose: {verbose}")

if verbose:
    print("Downloading Seasons Data...")
save_seasons_data(verbose)

# Loads the parquet file and starts downloading the jsons for the games

all_games = pd.read_parquet("data_downloads/games.parquet")["game_id"]
if verbose:
    logger.info("Saving the play-by-play jsons...")
    logger.info(f"Total games to download: {len(all_games)}")
    
for game_id in all_games:
    save_json_from_game(game_id, v=verbose)

logger.info("Job Completed")