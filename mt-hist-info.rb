#!/usr/bin/ruby

=begin
Purpose:
    Display basic info about MetaTrader .hst files and optionally:
    - run consistency check on them;
    - graph results of that check using gnuplot.
Author: Wejn <wejn at box dot cz>
License: GPLv2 (without the "latter" option)
Requires: Ruby >= 1.8
TS: 20080515213000

Example:

$ ./mt-hist-info.rb M1_EURUSD.hst --check
Version: 400
Copyright: Copyright Š 2005, Alpari Ltd.
Symbol: EURUSD
Period: 1
Digits: 4
Timesign: 0
LastSync: 0
Unused: 0
First record:
  Time: 2004-06-16 12:55:00
  Open: 1.2113
  Low: 1.2112
  High: 1.2115
  Close: 1.2115
  Volume: 15.0000
Last record:
  Time: 2008-04-12 00:59:00
  Open: 1.5813
  Low: 1.5807
  High: 1.5813
  Close: 1.5807
  Volume: 5.0000
Running consistency check, hold on ...
Total 128867 gaps within 1199307 records (10.75%) encountered.
Breakdown by occurence (gap size: count):
     1:  86250
     2:  23759
     3:   9064
     4:   4182
     5:   2168
     6:   1142
     7:    722
     8:    461
[...snip...]
=end

require 'optparse'
require 'ostruct'

HDRSIZE = 148
RECSIZE = 4 + 5*8
HST_VERSION = 400

# Properly format given value based on class
def format_value(value, digits)
    case value.class.to_s.to_sym
    when :String, :Integer
        value.to_s
    when :Float
        "%.#{digits}f" % [value]
    when :Time, :Date
        value.strftime("%Y-%m-%d %H:%M:%S")
    else
        value.to_s
    end
end

# Parse (read) record from file
def read_record(f, throw_exception = true)
    rec = f.read(::RECSIZE)
    unless rec && rec.size == ::RECSIZE
        raise "no record found" if throw_exception
        return nil
    end
    out = rec.unpack("ld*")
    out[0] = Time.at(out.first)
    out
end

# Display given record
def show_record(rec, digits, offset = 0)
    for label, value in %w[Time Open Low High Close Volume].zip(rec)
        puts " "*offset + label + ": " + format_value(value, digits)
    end
end

# Here we store settings
Settings = OpenStruct.new

# Setup option parser
opts = OptionParser.new do |opts| # {{{1
    opts.banner = "Usage: #{File.basename($0)} [options] <file.hst>"
    opts.separator "Available options:"

    opts.on('-c', '--check', "Check file for consistency") do
        Settings.check = true
    end

    opts.on('-v', '--verbose', "Turn on verbose mode") do
        Settings.verbose = true
    end

    opts.on('-g', '--graph', "Graph result of -c, implies -c") do
        Settings.check = true
        Settings.graph = true
    end

    opts.on_tail('-h', '--help', 'Show this message') do
        $stderr.puts opts
        exit 0
    end
end # }}}1

# Parse arguments
opts.parse!(ARGV)

infile = ARGV.shift

unless infile && FileTest.exists?(infile)
    if infile.nil?
        $stderr.puts "You must specify input file, do --help for usage."
    else
        $stderr.puts "Wrong input file: #{infile}"
    end
    exit 1
end

unless ARGV.size.zero?
    $stderr.puts "Extra (unknown?) parameters: #{ARGV.join(' ')}"
    exit 1
end

# Open the file...
File.open(infile) do |f|
    # Read header
    hdr = f.read(::HDRSIZE)
    raise "File too short while reading header" unless hdr.size == ::HDRSIZE
    vers, copy, symbol, period, digits, timesign, last_sync, *unused = all_flds = hdr.unpack('lA64A12l*')
    raise "Unsupported version: #{vers}" unless vers == ::HST_VERSION

    # Display header info
    for label, value in %w[Version Copyright Symbol Period Digits Timesign LastSync Unused].zip(all_flds)
        puts label + ": " + format_value(value, digits)
    end

    # Read first and last record
    first_rec = nil
    last_rec = nil

    # Read first and last record, ignoring any errors
    first_rec = read_record(f, false)
    if first_rec
        f.seek(-(::RECSIZE), IO::SEEK_END)
        last_rec = read_record(f, false)
    end

    # Display info
    unless first_rec && last_rec
        puts "No records found."
    else
        puts "First record:"
        show_record(first_rec, digits, 2)
        puts "Last record:"
        show_record(last_rec, digits, 2)
    end

    # Do check if requested
    if Settings.check
        puts "Running consistency check, hold on ..."

        # check all records for consistency
        last_ts = first_rec.first
        gaps = 0
        gap_sizes = Hash.new(0)
        gap_at = Hash.new(0)
        records = 0
        order_alert = true
        f.seek(::HDRSIZE, IO::SEEK_SET)
        while rec = read_record(f, false)
            records += 1

            # If there's ordering error
            if last_ts > rec.first && !order_alert
                order_alert = true
                puts "Record ordering fucked up (#{format_value(last_ts, digits)} > #{format_value(rec.first, digits)}) -- will screw up gap detection."
                puts "Expect no further complaints about ordering."
            end

            # If there's a gap...
            if last_ts + period*60 < rec.first
                gaps += 1
                gs = ((rec.first - last_ts)/(period*60)).to_i - 1
                gap_sizes[gs] += 1
                gap_at[last_ts] = gs
                puts "GAP: #{format_value(last_ts, digits)} -- #{format_value(rec.first, digits)}" if Settings.verbose
            end
            last_ts = rec.first
        end

        # Report what you found
        puts if Settings.verbose
        if gaps.zero?
            puts "No gaps encountered, wow!."
        else
            puts "Total #{gaps} gaps within #{records} records (#{format_value(gaps.to_f / (records.to_f / 100), 2)}%) encountered."
            puts "Breakdown by occurence (gap size: count):"
            for size, times in gap_sizes.sort_by { |k ,v| [-v, k] }
                puts("%6d: %6d" % [size, times])
            end
        end

def do_graph(outf, dataf, title, opts = {})
    plotdef = "\"#{dataf}\" using 1:2 title \"#{title}\" with #{opts[:style] ? opts[:style] : "impulses"}"

    IO.popen('gnuplot', 'w') do |f|
        f.puts <<-EOF
set terminal png size #{opts[:size] ? opts[:size] : "1024,768"}
set output "#{outf}"
        EOF
        f.puts "set logscale x" if opts[:x_log]
        f.puts "set logscale y" if opts[:y_log]

        f.puts "set xlabel \"#{opts[:x_label]}\"" if opts[:x_label]
        f.puts "set ylabel \"#{opts[:y_label]}\"" if opts[:y_label]

        if opts[:x_time]
            f.puts <<-EOF
set timefmt "%s"
set xdata time
set format x "%d\\n%m\\n%Y"
            EOF
        end

        f.puts <<-EOF
plot #{plotdef}
quit
        EOF
    end
end


        # Optionally graph
        if Settings.graph
            puts
            puts "Running graph generation, hold on ..."

            # Graph gapsizes
            begin
                fn = infile + ".gap_sizes"
                File.open(fn, "w") do |f|
                    for size, times in gap_sizes.sort_by { |k ,v| k }
                        f.puts "#{size} #{times}"
                    end
                end

                do_graph(fn + ".png", fn, "Gap size distribution", :x_log => true, :y_log => true, :x_label => "gap size", :y_label => "gap occurence")

                puts "Successfully wrote: #{fn}.png"
            ensure
                File.unlink(fn) rescue nil
            end

            # Graph placements
            begin
                fn = infile + ".gap_at"
                File.open(fn, "w") do |f|
                    for time, size in gap_at.sort_by { |k ,v| k }
                        f.puts "#{time.to_i} #{size}"
                    end
                end

                do_graph(fn + ".png", fn, "Gap placement (in time)", :y_log => true, :x_label => "gap start", :y_label => "gap size", :x_time => true, :size => "10240,768")

                puts "Successfully wrote: #{fn}.png"
            ensure
                File.unlink(fn) rescue nil
            end
        end
    end
end
