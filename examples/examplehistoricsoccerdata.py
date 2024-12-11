from pathlib import Path
import logging

import betfairlightweight
import argparse
import time

"""
Historic is the API endpoint that can be used to
download data betfair provide.

https://historicdata.betfair.com/#/apidocs
"""

parser = argparse.ArgumentParser()

parser.add_argument("-fd", "--from-day", type=int, dest="from_day", help="The start day of the scan", default=1)
parser.add_argument("-fm", "--from-month",type=int, dest="from_month", help="The start month of the scan", default=1)
parser.add_argument("-fy", "--from-year",type=int, dest="from_year",  help="The start year of the scan", default=2023)

parser.add_argument("-td", "--to-day",type=int, dest="to_day",  help="The end day of the scan", default=1)
parser.add_argument("-tm", "--to-month",type=int, dest="to_month", help="The end month of the scan", default=1)
parser.add_argument("-ty", "--to-year",type=int, dest="to_year", help="The end year of the scan", default=2023)

parser.add_argument("-m", "--market", dest="market", help="The market to store", default="OVER_UNDER_25")

parser.add_argument("-dr","--dry-run",dest="dry_run", action="store_true", help="Run a dry run")


args = parser.parse_args()

# setup logging
logging.basicConfig(level=logging.INFO)  # change to DEBUG to see log all updates

# create trading instance

trading = betfairlightweight.APIClient("XXXX", "XXXX", app_key="XXXX", certs='XXXX')

# login
trading.login()

# get collection options (allows filtering)
# collection_options = trading.historic.get_collection_options(
#     "Soccer", "Basic Plan", args.from_day, args.from_month, args.from_year, args.to_day, args.to_month, args.to_year
# )
# print(collection_options)

# get file list
file_list = trading.historic.get_file_list(
    "Soccer",
    "Basic Plan",
    from_day=args.from_day,
    from_month=args.from_month,
    from_year=args.from_year,
    to_day=args.to_day,
    to_month=args.to_month,
    to_year=args.to_year,
    # event_id=31954039,
    market_types_collection=[args.market],
    countries_collection=["GB"],
    file_type_collection=["M"],
)
print(file_list)
if not args.dry_run:
    for file in file_list:
        print(file)
        file_split = file.split("/")
        type = str.lower(args.market)
        day = file_split[6]
        month = file_split[5]
        year = file_split[4]
        directory = f"data/BASIC/{type}/{day}/{month}/{year}"
        print(directory)
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Directory /BASIC/TYPE/DAY/MONTH/YEAR
        time.sleep(1)
        download = trading.historic.download_file(file_path=file,store_directory=directory)
        # print(download)
