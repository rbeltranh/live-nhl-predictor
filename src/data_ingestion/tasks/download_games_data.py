import argparse
import logging
from config import DEFAULT_VERBOSE
from api_call_functions import save_seasons_data

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