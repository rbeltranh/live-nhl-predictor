import argparse
import pandas as pd
import logging
from config import DEFAULT_VERBOSE, DEFAULT_GAMES_FILE_PATH
from api_call_functions import save_json_from_game

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.Logger("DownloaderLogger")
logger.addHandler(console_handler)

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", default=DEFAULT_VERBOSE)
args = parser.parse_args()

verbose = args.verbose



all_games = pd.read_parquet(DEFAULT_GAMES_FILE_PATH)["game_id"]
if verbose:
    logger.info("Saving the play-by-play jsons...")
    logger.info(f"Total games to download: {len(all_games)}")
    
for game_id in all_games:
    save_json_from_game(game_id, v=verbose)
