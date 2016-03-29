PATH  := "$(PATH):$(PWD)"
SHELL := env PATH=$(PATH) /bin/bash -xe
xargs := $(shell which gxargs xargs | head -n1)
pair    = EURUSD
year 	  = 2014
server  = FX
dl_dir  = download/ds
csvfile = ticks.csv
spread=20

# HST files.
m1_hst=$(pair)1.hst
m5_hst=$(pair)5.hst
m15_hst=$(pair)15.hst
m30_hst=$(pair)30.hst
h1_hst=$(pair)60.hst
h4_hst=$(pair)240.hst
d1_hst=$(pair)1440.hst
w1_hst=$(pair)10080.hst
mn_hst=$(pair)43200.hst

# FXT files.
m1_fxt=$(pair)1_0.fxt
m5_fxt=$(pair)5_0.fxt
m15_fxt=$(pair)15_0.fxt
m30_fxt=$(pair)30_0.fxt
h1_fxt=$(pair)60_0.fxt
h4_fxt=$(pair)240_0.fxt
d1_fxt=$(pair)1440_0.fxt
w1_fxt=$(pair)10080_0.fxt
mn_fxt=$(pair)43200_0.fxt

test: test-help $(m1_hst) $(m1_fxt) test-dump-hst test-dump-fxt

$(dl_dir)/$(pair)/$(year)/01: dl_bt_dukascopy.py
	dl_bt_dukascopy.py -v -p ${pair} -y ${year} -m 1 -c -d $(dl_dir)

test-dump-hst:
	find . -name "*.hst" -execdir convert_mt_to_csv.py -i {} -f hst4 -o {}.csv ';'

test-dump-fxt:
	find . -name "*.fxt" -execdir convert_mt_to_csv.py -i {} -f fxt4 -o {}.csv ';'

test-help: convert_csv_to_mt.py dl_bt_dukascopy.py convert_mt_to_csv.py
	python3 convert_csv_to_mt.py --help
	python3 dl_bt_dukascopy.py --help
	python3 convert_mt_to_csv.py --help

# Generate HST files.
$(m1_hst): $(csvfile) convert_csv_to_mt.py
	convert_csv_to_mt.py -v -i $(csvfile) -s $(pair) -p $(spread) -S default -t M1,M5,M15,M30,H1,H4,D1,W1,MN -f hst4

# Generate FXT files.
$(m1_fxt): $(csvfile) convert_csv_to_mt.py
	convert_csv_to_mt.py -v -i $(csvfile) -s $(pair) -p $(spread) -S default -t M1,M5,M15,M30,H1,H4,D1,W1,MN -f fxt4

$(csvfile): $(dl_dir)/$(pair)/$(year)/01
	find . -name '*.csv' -print0 | sort -z | $(xargs) -r0 cat | tee $(csvfile) > /dev/null
# find . -name '*.csv' -print0 | sort -z | $(xargs) -r0 cat | tee $(csvfile) | pv -ps $(size) > /dev/null
