#!/usr/bin/env python3

import argparse
import sys
import datetime
import csv
import random

def error(message, exit=True):
    print('[ERROR]', message)
    if exit: sys.exit(1)


def volumesFromTimestamp(timestamp, spread):
    longTimestamp = timestamp.timestamp()
    spread *= 1e5
    d = int(str(int(longTimestamp/60))[-3:]) + 1
    bidVolume = int((longTimestamp/d)%(1e3 - spread))

    return (bidVolume, bidVolume + spread)


def linearModel(startDate, endDate, startPrice, endPrice, deltaTime, spread, digits):
    timestamp = startDate
    bidPrice = startPrice
    askPrice = bidPrice + spread
    bidVolume = 1
    askVolume = bidVolume + spread
    deltaPrice = deltaTime/(endDate + datetime.timedelta(days=1) - startDate - deltaTime)*(endPrice - startPrice)
    rows = []
    while timestamp < (endDate + datetime.timedelta(days=1)):
        rows += [{
            'timestamp': timestamp,
             'bidPrice': bidPrice,
             'askPrice': askPrice,
            'bidVolume': bidVolume,
            'askVolume': askVolume
        }]
        timestamp += deltaTime
        bidPrice += deltaPrice
        askPrice += deltaPrice
        (bidVolume, askVolume) = volumesFromTimestamp(timestamp, spread)
    return rows


def randomModel(startDate, endDate, startPrice, endPrice, deltaTime, spread, volatility):
    timestamp = startDate
    bidPrice = startPrice
    askPrice = bidPrice + spread
    bidVolume = 1
    askVolume = bidVolume + spread
    rows = []
    while timestamp < (endDate + datetime.timedelta(days=1)):
        rows += [{
            'timestamp': timestamp,
             'bidPrice': bidPrice,
             'askPrice': askPrice,
            'bidVolume': bidVolume,
            'askVolume': askVolume
        }]
        timestamp += deltaTime
        bidPrice = 1 + volatility*random.random()
        askPrice = bidPrice + spread
        (bidVolume, askVolume) = volumesFromTimestamp(timestamp, spread)
    rows[-1]['bidPrice'] = endPrice
    rows[-1]['askPrice'] = endPrice + spread
    return rows


def writeToCsv(rows, filename):
    with open(filename, 'w') as csvOutput:
        csvWriter = csv.writer(csvOutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            csvWriter.writerow([
                row['timestamp'].strftime('%Y.%m.%d %H:%M:%S.%f')[:-3],
                round(row['bidPrice'], 5),
                round(row['askPrice'], 5),
                round(row['bidVolume'], 2),
                round(row['askVolume'], 2)
            ])


def dump(rows):
    for row in rows:
        print('%s,%.5f,%.5f,%.2f,%.2f' % (
            row['timestamp'].strftime('%Y.%m.%d %H:%M:%S.%f')[:-3],
            row['bidPrice'],
            row['askPrice'],
            row['bidVolume'],
            row['askVolume']
        ))


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument('startDate',
                                help='Starting date of generated data in YYYY.MM.DD format.')
    argumentParser.add_argument('endDate',
                                help='Ending date of generated data in YYYY.MM.DD format.')
    argumentParser.add_argument('startPrice',
                                type=float,
                                help='Starting bid price of generated data, must be a float value.')
    argumentParser.add_argument('endPrice',
                                type=float,
                                help='Ending bid price of generated data, must be a float value.')
    argumentParser.add_argument('-D', '--digits',
                                type=int,
                                action='store',
                                dest='digits',
                                help='Decimal digits of prices.',
                                default=5)
    argumentParser.add_argument('-s', '--spread',
                                type=int,
                                action='store',
                                dest='spread',
                                help='Spread between prices in points.',
                                default=10)
    argumentParser.add_argument('-d', '--density',
                                type=int,
                                action='store',
                                dest='density',
                                help='Data points per minute in generated data.',
                                default=1)
    argumentParser.add_argument('-p', '--pattern',
                                action='store',
                                dest='pattern',
                                choices=['none', 'wave', 'curve', 'zigzag', 'random'],
                                help='Modelling pattern, all of them are deterministic except of \'random\'.', default='none')
    argumentParser.add_argument('-v', '--volatility',
                                type=float,
                                action='store',
                                dest='volatility',
                                help='Volatility gain for models, higher values leads to higher volatility in price values.',
                                default=1.0)
    argumentParser.add_argument('-o', '--outputFile',
                                action='store',
                                dest='outputFile',
                                help='Write generated data to file instead of standard output.')
    arguments = argumentParser.parse_args()

    # Check date values
    try:
        startDate = datetime.datetime.strptime(arguments.startDate, '%Y.%m.%d')
        endDate   = datetime.datetime.strptime(arguments.endDate,   '%Y.%m.%d')
    except ValueError as e:
        error('Bad date format!')

    if endDate < startDate: error('Ending date precedes starting date!')

    if arguments.digits <= 0: error('Digits must be larger than zero!')

    if arguments.startPrice <= 0 or arguments.endPrice <= 0: error('Price must be larger than zero!')

    if arguments.spread < 0: error('Spread must be larger or equal to zero!')
    spread = arguments.spread/1e5

    if arguments.density <= 0: error('Density must be larger than zero!')

    if arguments.volatility <= 0: error('Volatility must be larger than zero!')

    # Select and run appropriate model
    deltaTime = datetime.timedelta(seconds=60/arguments.density)
    rows = None
    if arguments.pattern == 'none':
        rows = linearModel(startDate, endDate, arguments.startPrice, arguments.endPrice, deltaTime, spread, arguments.digits)
    elif arguments.pattern == 'random':
        rows = randomModel(startDate, endDate, arguments.startPrice, arguments.endPrice, deltaTime, spread, arguments.volatility)

    # output array stdout/file
    if arguments.outputFile:
        writeToCsv(rows, arguments.outputFile)
    else:
        dump(rows)
