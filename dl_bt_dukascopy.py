#!/usr/bin/env python3
# Sample usage:
#   ./dl_bt_dukascopy.py -p EURUSD -y 2013,2014

import sys
import os
import argparse
import datetime
import time
import urllib.request
from urllib.error import HTTPError,ContentTooShortError
import lzma

# Create a mapping of currencies.
all_currencies = {
    "AUDJPY": 1175270400, # starting from 2007.03.30 16:00
    "AUDNZD": 1229961600, # starting from 2008.12.22 16:00
    "AUDUSD": 1175270400, # starting from 2007.03.30 16:00
    "CADJPY": 1175270400, # starting from 2007.03.30 16:00
    "CHFJPY": 1175270400, # starting from 2007.03.30 16:00
    "EURAUD": 1175270400, # starting from 2007.03.30 16:00
    "EURCAD": 1222167600, # starting from 2008.09.23 11:00
    "EURCHF": 1175270400, # starting from 2007.03.30 16:00
    "EURGBP": 1175270400, # starting from 2007.03.30 16:00
    "EURJPY": 1175270400, # starting from 2007.03.30 16:00
    "EURNOK": 1175270400, # starting from 2007.03.30 16:00
    "EURSEK": 1175270400, # starting from 2007.03.30 16:00
    "EURUSD": 1175270400, # starting from 2007.03.30 16:00
    "GBPCHF": 1175270400, # starting from 2007.03.30 16:00
    "GBPJPY": 1175270400, # starting from 2007.03.30 16:00
    "GBPUSD": 1175270400, # starting from 2007.03.30 16:00
    "NZDUSD": 1175270400, # starting from 2007.03.30 16:00
    "USDCAD": 1175270400, # starting from 2007.03.30 16:00
    "USDCHF": 1175270400, # starting from 2007.03.30 16:00
    "USDJPY": 1175270400, # starting from 2007.03.30 16:00
    "USDNOK": 1222639200, # starting from 2008.09.28 22:00
    "USDSEK": 1222642800, # starting from 2008.09.28 23:00
    "USDSGD": 1222642800, # starting from 2008.09.28 23:00
    "AUDCAD": 1266318000, # starting from 2010.02.16 11:00
    "AUDCHF": 1266318000, # starting from 2010.02.16 11:00
    "CADCHF": 1266318000, # starting from 2010.02.16 11:00
    "EURNZD": 1266318000, # starting from 2010.02.16 11:00
    "GBPAUD": 1266318000, # starting from 2010.02.16 11:00
    "GBPCAD": 1266318000, # starting from 2010.02.16 11:00
    "GBPNZD": 1266318000, # starting from 2010.02.16 11:00
    "NZDCAD": 1266318000, # starting from 2010.02.16 11:00
    "NZDCHF": 1266318000, # starting from 2010.02.16 11:00
    "NZDJPY": 1266318000, # starting from 2010.02.16 11:00
    "XAGUSD": 1289491200, # starting from 2010.11.11 16:00
    "XAUUSD": 1305010800, # starting from 2011.05.10 07:00
}

class Dukascopy:
    url_tpl = "http://www.dukascopy.com/datafeed/%s/%04d/%02d/%02d/%02dh_ticks.bi5"

    def __init__(self, pair, year, month, day, hour, dest = "download"):
        if not os.path.exists(dest):
            os.mkdir(dest)
        self.url = self.url_tpl % (pair, int(year), month, day, hour)
        self.path = "%s/%04d-%02d-%02d--%02dh_ticks.bi5" % (dest, year, month, day, hour)

    def download(self):
        print("Downloading %s into: %s..." % (self.url, self.path))
        if os.path.isfile(self.path):
            print("File exists.");
            return True
        else:
            try:
                urllib.request.urlretrieve(self.url, filename=self.path)
            except HTTPError as err:
                if err.code == 404:
                    print("Error: %s, reason: %s." % (err.code, err.reason));
                    return False
            except ContentTooShortError as err:
                print("Error: The downloaded data is less than the expected amount, so ignoring.")
                return False
        return True

    def bt5_to_csv(self):
        with open(self.path, 'r') as f:
            data = f.read()
        new_path = self.path.replace("bi5", "csv")
        print("Converting into CSV (%s)..." % (new_path))
        # todo
        output = lzma.decompress(data)
        # todo
        with open(new_path, 'w') as f:
            f.write(output)

if __name__ == '__main__':

    # Parse arguments.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-?", "--help",         action="help",                         help="Show this help message and exit." )
    parser.add_argument("-v", "--verbose",      action="store_true", dest="verbose",   help="Increase output verbosity." )
    parser.add_argument("-d", "--download-dir", action="store",      dest="dest",      help="Directory to download files.", default="download")
    parser.add_argument("-p", "--pairs",        action="store",      dest="pairs",     help="Pair(s) to download (separated by comma).", default="all")
    parser.add_argument("-y", "--years",        action="store",      dest="years",     help="Year(s) to download (separated by comma).", default="all")
    args = parser.parse_args()

    curr_year = datetime.date.today().year
    pairs = list(all_currencies.keys()) if args.pairs == "all" else args.pairs.split(',')
    years = range(1997, curr_year+1) if args.years == "all" else args.years.split(',')

    try:
        currencies = []
        for pair in sorted(pairs):
            for year in sorted(years):
                for month in range(1, 12+1):
                    for day in range(1, 31+1):
                        for hour in range(0, 23+1):
                            try:
                                dt = datetime.datetime(year=int(year), month=month, day=day, hour=hour)
                                unix = time.mktime(dt.timetuple())
                                if unix > all_currencies.get(pair) and unix < time.time(): # Validate dates.
                                    ds = Dukascopy(pair, int(year), month, day, hour, dest=args.dest + "/" + pair)
                                    ds.download()
                                    #ds.bt5_to_csv() #todo
                                    #raise KeyboardInterrupt # perform one record for testing
                            except ValueError: # Ignore invalid dates.
                                continue
    except KeyboardInterrupt:
        sys.exit()
