#!/usr/bin/env python3

import argparse
import sys
import datetime
import csv

def error(message, exit=True):
    print('[ERROR]', message)
    if exit: sys.exit(1)


def linearModel(startDate, endDate, startPrice, endPrice, deltaTime, spread, digits):
    timestamp = startDate
    bidPrice = startPrice
    askPrice = bidPrice + spread
    bidVolume = 0   # TODO -v
    askVolume = 0   # TODO -v
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
                                help='TODO',
                                default=10)
    argumentParser.add_argument('-d', '--density',
                                type=int,
                                action='store',
                                dest='density',
                                help='TODO',
                                default=1)
    argumentParser.add_argument('-p', '--pattern',
                                action='store',
                                dest='pattern',
                                choices=['none', 'wave', 'curve', 'zigzag', 'random'],
                                help='TODO', default='none')
    # TODO -v argument
    argumentParser.add_argument('-o', '--outputFile', action='store', dest='outputFile',       help='TODO')
    arguments = argumentParser.parse_args()

    # Check date values
    try:
        startDate = datetime.datetime.strptime(arguments.startDate, '%Y.%m.%d')
        endDate   = datetime.datetime.strptime(arguments.endDate,   '%Y.%m.%d')
    except ValueError as e:
        error('Bad date format!')

    if endDate < startDate: error('Ending date precedes starting date!')

    if arguments.digits <= 0: error('Digits must be larger than zero!')

    if arguments.spread < 0: error('Spread must be larger or equal to zero!')
    spread = arguments.spread/1e5

    if arguments.density <= 0: error('Density must be larger than zero!')

    deltaTime = datetime.timedelta(seconds=60/arguments.density)

    # Select and run appropriate model
    rows = None
    if arguments.pattern == 'none':
        rows = linearModel(startDate, endDate, arguments.startPrice, arguments.endPrice, deltaTime, spread, arguments.digits)

    # output array stdout/file
    if arguments.outputFile:
        writeToCsv(rows, arguments.outputFile)
    else:
        dump(rows)
