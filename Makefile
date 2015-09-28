SHELL := /bin/bash -x
symbol = EURUSD
year = 2014
server = FX
dl_dir = download/dukascopy
test: test-help test-download test-convert test-dump-hst test-dump-fxt

test-download: $(dl_dir)/$(symbol)/01/%.csv
$(dl_dir)/$(symbol)/01/%.csv:
	python3 dl_bt_dukascopy.py -v -p ${symbol} -y ${year} -m 1 -c -d $(dl_dir)

test-convert: M1/%.hst M1/%.fxt M5/%.hst M5/%.fxt

M1/%.hst: TF = M1
M1/%.hst: dukascopy.csv
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4_509 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f fxt4 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4 

M1/%.fxt: TF = M1
M1/%.fxt: dukascopy.csv
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4_509 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f fxt4 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4 

M5/%.hst: TF = M5
M5/%.hst: dukascopy.csv
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4_509 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4 

M5/%.fxt: TF = M5
M5/%.fxt: dukascopy.csv
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4_509 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f fxt4 
	python3 convert_csv_to_mt.py -i dukascopy.csv -s ${symbol} -p 10 -S ${server} -t ${TF} -d ${TF} -f hst4 

test-dump-hst: M1/${symbol}1.hst M5/${symbol}5.hst
	find . -name "*.hst" -execdir python3 `realpath convert_mt_to_csv.py` -i {} -f hst4 -o {}.csv ';'

test-dump-fxt: M1/${symbol}1_0.fxt M5/${symbol}5_0.fxt
	find . -name "*.fxt" -execdir python3 `realpath convert_mt_to_csv.py` -i {} -f fxt4 -o {}.csv ';'

test-help:
	python3 convert_csv_to_mt.py --help
	python3 dl_bt_dukascopy.py --help
	python3 convert_mt_to_csv.py --help

dukascopy.csv:
	find download/dukascopy/${symbol}/${year} -name "*.csv" -exec cat {} '+' > dukascopy.csv
