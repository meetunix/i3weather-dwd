#!/usr/bin/env python3
""" station-lookup - searches the DWD-weather-station catalogue inplace

Copyright © 2020 Martin Steinbach

See file LICENSE for license information
"""

import sys
import re
import urllib.request

# Quelle: Deutscher Wetterdienst
ALL_STATION_URL = 'https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication&nn=16102'
AVAILABLE_STATIONS_URL = 'https://opendata.dwd.de/weather/weather_reports/poi/'

def get_file_from_url(url):
    response = urllib.request.urlopen(url)
    #print("returned status: {} - file size: {}".
    #    format(response.status,response.getheader("Content-Length")))
    if response.status != 200:
        return None
    else:
        return response.read()
    
def get_testfile(path):
    fb = open(path,"rb")
    f = fb.read()
    fb.close()
    return f

def build_stations_dict(stat_list, avail_stat_list):
    stations_dict = {}
    for l in stat_list:
        if re.match('^9',l):
            l = l[12:]
            sId = l.split(' ')[0]
            if sId in avail_stat_list:
                place = l[11:32].strip().lower() 
                stations_dict.update({sId : place})
    return stations_dict

def build_available_stations_list(ll):
    available_stations = []
    for l in ll:
        if re.match('^<a href',l):
            l = l.split("\"")
            l = l[1].split("-")[0].replace("_"," ").strip()
            available_stations.append(l)
    return available_stations

def convert_umlauts (search_input):
    
    umlauts = {
            b'\xc3\xa4': b'ae',  # U+00E4
            b'\xc3\xb6': b'oe',  # U+00F6
            b'\xc3\xbc': b'ue',  # U+00FC
            b'\xc3\x84': b'Ae',  # U+00C4
            b'\xc3\x96': b'Oe',  # U+00D6
            b'\xc3\x9c': b'Ue',  # U+00DC
            b'\xc3\x9f': b'ss',  # U+00DF
            }

    search_utf8 = search_input.encode('utf-8')

    for umlaut in umlauts.keys():
        search_utf8 = search_utf8.replace(umlaut,umlauts[umlaut])
   
    return search_utf8.decode()

def main(search):
    
    avail_stations = get_file_from_url(AVAILABLE_STATIONS_URL)
    avail_stations = avail_stations.decode('utf_8').splitlines()
    avail_stations = build_available_stations_list(avail_stations)

    stations = get_file_from_url(ALL_STATION_URL)
    #stations = get_testfile('mosmix_stationskatalog.cfg') 
    stations = stations.decode("iso8859-1").splitlines()
    stations_dict = build_stations_dict(stations, avail_stations)

    search = search.strip().lower()
    search = convert_umlauts(search)
    pattern = '.*'+search+'.*'
    pattern = re.compile(pattern)
    matches = 0
    for key, place in stations_dict.items():
        if re.match(pattern,place):
            matches += 1
            print("{:5} <--> {}".format(key,place))

    if matches == 0:
        print("no station found")


if __name__ == "__main__":
    main(sys.argv[1])

