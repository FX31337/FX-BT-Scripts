from bstruct import *

#
# Structure definitions
#
class TicksRaw(BStruct):
    _endianness = '<'
    _fields = [
            ('symbol', '12s', pretty_print_string),
            ('time', 'I', pretty_print_time),
            ('bid', 'd'),
            ('ask', 'd'),
            ('counter', 'I'),
            ('unknown', 'I'),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 40)

class SymbolSel(BStruct):
    _endianness = '<'
    _fields = [
            ('symbol', '12s', pretty_print_string),
            ('digits', 'I'),
            ('index', 'I'),
            ('unknown_1', 'I'),
            ('group', 'I'),
            ('unknown_2', 'I'),
            ('pointSize', 'd'),
            ('spread', 'I'),
            ('unknown_3', 'I'),
            ('tickType', 'I'),
            ('unknown_4', 'H'),
            ('unknown_5', 'H'),
            ('time', 'I', pretty_print_time),
            ('unknown_6', 'I'),
            ('bid', 'd'),
            ('ask', 'd'),
            ('sessionHigh', 'd'),
            ('sessionLow', 'd'),
            ('unknown_17', '16s', pretty_print_compact),
            ('bid_2', 'd'),
            ('ask_2', 'd')
            ]
    _size = get_fields_size(_fields)
    assert(_size == 128)

class Symgroups(BStruct):
    _endianness = '<'
    _fields = [
            ('name', '16s', pretty_print_string),
            ('description', '60s', pretty_print_string),
            ('backgroundColor', 'I')
            ]
    _size = get_fields_size(_fields)
    assert(_size == 80)

class SymbolsRaw(BStruct):
    _endianness = '<'
    _fields = [
            ('name', '12s', pretty_print_string),
            ('description', '64s', pretty_print_string),
            ('altName', '12s', pretty_print_string),
            ('baseCurrency', '12s', pretty_print_string),
            ('group', 'I'),
            ('digits', 'I'),
            ('tradeMode', 'I'),
            ('backgroundColor', 'I', pretty_print_hex),
            ('id', 'I'),
            ('unknown_1', '1508c', pretty_print_ignore),
            ('unknown_2', 'I'),
            ('unknown_3', '8c'),
            ('unknown_4', 'd'),
            ('unknown_5', '12s', pretty_print_compact),
            ('spread', 'I'),
            ('unknown_6', '16s', pretty_print_compact),
            ('swapLong', 'd'),
            ('swapShort', 'd'),
            ('unknown_7', 'I'),
            ('unknown_8', 'I'),
            ('contractSize', 'd'),
            ('unknown_9', '16s', pretty_print_compact),
            ('stopDistance', 'I'),
            ('unknown_10', '12s', pretty_print_compact),
            ('marginInit', 'd'),
            ('marginMaintenance', 'd'),
            ('marginHedged', 'd'),
            ('marginDivider', 'd'),
            ('pointSize', 'd'),
            ('pointsPerUnit', 'd'),
            ('unknown_11', '24s', pretty_print_compact),
            ('marginCurrency', '12s', pretty_print_string),
            ('unknown_12', '104s', pretty_print_ignore),
            ('unknown_13', 'I'),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 1936)

class FxtHeader(BStruct):
    _endianness = '<'
    _fields = [
            # Build header
            ('headerVersion', 'I'),
            ('copyright', '64s', pretty_print_string),
            ('server', '128s', pretty_print_string),
            ('symbol', '12s', pretty_print_string),
            ('timeframe', 'i'),
            ('modelType', 'i'),
            ('totalBars', 'I'),
            ('modelStart', 'I', pretty_print_time),
            ('modelEnd', 'I', pretty_print_time),
            ('padding1', '4s', pretty_print_ignore),

            # General parameters
            ('modelQuality', 'd'),
            ('baseCurrency', '12s', pretty_print_string),
            ('spread', 'I'),
            ('digits', 'I'),
            ('padding2', '4s', pretty_print_ignore),
            ('pointSize', 'd'),
            ('minLotSize', 'i'),
            ('maxLotSize', 'i'),
            ('lotStep', 'i'),
            ('stopLevel', 'i'),
            ('GTC', 'i'),
            ('padding3', '4s', pretty_print_ignore),

            # Profit Calculation parameters
            ('contractSize', 'd'),
            ('tickValue', 'd'),
            ('tickSize', 'd'),
            ('profitMode', 'i'),
            ('swapEnabled', 'i'),
            ('swapMethod', 'i'),
            ('padding4', '4s', pretty_print_ignore),
            ('swapLong', 'd'),
            ('swapShort', 'd'),
            ('swapRollover', 'i'),

            # Margin calculation
            ('accountLeverage', 'i'), # Default: 100
            ('freeMarginMode', 'i'),
            ('marginCalcMode', 'i'),
            ('marginStopoutLevel', 'i'),
            ('marginStopoutMode', 'i'),
            ('marginRequirements', 'd'),
            ('marginMaintenanceReq', 'd'),
            ('marginHedgedPosReq', 'd'),
            ('marginLeverageDivider', 'd'),
            ('marginCurrency', '12s', pretty_print_string),
            ('padding5', '4s', pretty_print_ignore),

            # Commission calculation
            ('commission', 'd'),
            ('commissionType', 'i'),
            ('commissionPerEntry', 'i'),

            # For internal use
            ('indexOfFirstBar', 'i'),
            ('indexOfLastBar', 'i'),
            ('indexOfM1Bar', 'i'),
            ('indexOfM5Bar', 'i'),
            ('indexOfM15Bar', 'i'),
            ('indexOfM30Bar', 'i'),
            ('indexOfH1Bar', 'i'),
            ('indexOfH4Bar', 'i'),
            ('beginDate', 'I', pretty_print_time),
            ('endDate', 'I', pretty_print_time),
            ('freezeLevel', 'i'),
            ('numberOfErrors', 'I'),
            ('reserved', '240s', pretty_print_ignore),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 728)

class HccHeader(BStruct):
    _endianness = '<'
    _fields = [
            ('magic', 'I'),
            ('copyright', '128s', pretty_print_wstring),
            ('name', '32s', pretty_print_wstring),
            ('title', '64s', pretty_print_wstring)
            ]
    _size = get_fields_size(_fields)
    assert(_size == 228)

class HccTable(BStruct):
    _endianness = '<'
    _fields = [
            ('unknown_0', 'I'),
            ('unknown_1', 'I', pretty_print_time),
            ('unknown_2', 'H'),
            ('size', 'I'),
            ('off',  'I', pretty_print_hex),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 18)

class HccRecordHeader(BStruct):
    _endianness = '<'
    _fields = [
            ('magic', 'H'),
            ('label', '64s', pretty_print_wstring),
            ('unknown_0', '18s', pretty_print_ignore),
            ('rows', 'I'),
            ('unknown_1', '101s', pretty_print_ignore),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 189)

class HccRecord(BStruct):
    _endianness = '<'
    _fields = [
            ('separator', 'I', pretty_print_ignore),
            ('time', 'I', pretty_print_time),
            ('open', 'd'),
            ('high', 'd'),
            ('low', 'd'),
            ('close', 'd'),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 40)


