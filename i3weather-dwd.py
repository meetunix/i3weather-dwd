#!/usr/bin/env python3

""" i3weather-dwd

i3status plugin for displaying weather information from the German Meteorological
Service (Deutscher Wetterdienst) without external dependencies.

Copyright © 2020 Martin Steinbach

See file LICENSE for license information
"""

import os
import sys
import csv
import argparse
import signal
import urllib.request
import resource as rsc
from time import sleep
from pathlib import Path

# Quelle: Deutscher Wetterdienst
DWD_POI_URL = "https://opendata.dwd.de/weather/weather_reports/poi/"

# FILE_PATH: Path to the file where the weather information is stored.
FILE_PATH = "/tmp/i3weather-dwd"

# Default path to pid file if no argument is passed to --pid:
PID_DEFAULT = "/tmp/i3weather-dwd.pid"

#https://www.dwd.de/DE/leistungen/opendata/help/schluessel_datenformate/bufr/
#poi_present_weather_zuordnung_pdf.pdf?__blob=publicationFile&v=2
# code -> (shortDescr, detailDescr, englishDescr)
PRESENT_WEATHER_CODES ={  
    "1" : ("wolkenlos","wolkenlos","clear"),
    "2" : ("heiter","heiter","bright"),
    "3" : ("bewölkt","bewoelkt","cloudy"),
    "4" : ("bedeckt","bedeckt","overcast"),
    "5" : ("Nebel","Nebel","fog"),
    "6" : ("Nebel","gefrierender Nebel","fog"),
    "7" : ("Regen","leichter Regen","rain (sprinkle)"),
    "8" : ("Regen","Regen","rain"),
    "9" : ("Regen","kräftiger Regen","heavy rain"),
    "10" : ("Schneeregen","gefrierender Regen","sleet"),
    "11" : ("Schneeregen","kraeftiger gefrierender Regen","sleet"),
    "12" : ("Schneeregen","Schneeregen","sleet"),
    "13" : ("Schneeregen","kraeftiger Schneeregen","sleet"),
    "14" : ("Schneefall","leichter Schneefall","snowfall"),
    "15" : ("Schneefall","Schneefall","snowfall"),
    "16" : ("Schneefall","kraeftiger Schneefall","snowfall"),
    "17" : ("Schneefall","Eiskoerner","hail"),
    "18" : ("Regenschauer","Regenschauer","rain shower"),
    "19" : ("Regenschauer","kraeftiger Regenschauer","rain shower"),
    "20" : ("Schneeregenschauer","Schneeregenschauer","heavy sleet"),
    "21" : ("Schneeschauer","kraeftiger Schneeregenschauer","heavy sleet"),
    "22" : ("Schneeschauer","Schneeschauer","snow shower"),
    "23" : ("Schneeschauer","kraeftiger Schneeschauer","heavy snow shower"),
    "24" : ("Schneeschauer","Graupelschauer","hail pellet shower"),
    "25" : ("Schneeschauer","kraeftiger Graupelschauer","heavy hail pellet shower"),
    "26" : ("Gewitter","Gewitter ohne Niederschlag","thunderstorm wo precipitation"),
    "27" : ("Gewitter","Gewitter","thunderstorm"),
    "28" : ("Gewitter","kraeftiges Gewitter","heavy thunderstorm"),
    "29" : ("Gewitter","Gewitter mit Hagel","thunderstorm with hail"),
    "30" : ("Gewitter","kraeftiges Gewitter mit Hagel","heavy thunderstorm with hail"),
    "31" : ("Sturm","Boen","storm")}

def daemonize():

    WORKDIR = "/tmp"
    UMASK = 0o033
    REDIRECT_FD = "/dev/null"

    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
        else:
            os.setsid()
            # second fork to be sure the process is no process group leader
    #        pid = os.fork()
    #        if pid != 0:
    #            sys.exit(0)
    #        else:
            os.chdir(WORKDIR)
            os.umask(UMASK)

    except OSError as e:
        sys.stderr.write("fork  failed: {} ({})\n".format(e.errno, e.strerror))
    
    return os.getpid()

def run_as_daemon(config):
   
    if config['pid'] != None:
        pid_path = Path(config['pid'])
    else:
        pid_path = Path(PID_DEFAULT)

    if pid_path.is_file():
        sys.stderr.write("PID-File {} already exists, closing ..\n"
                .format(pid_path))
        sys.exit(-1)
    else:
        pid = daemonize()
        pid_path.write_text(str(pid))

    return pid

def get_file_from_url(url):
    try:
        response = urllib.request.urlopen(url)
        #print("returned status: {} - file size: {}".
        #    format(response.status,response.getheader("Content-Length")))
    except urllib.error.HTTPError as e:
        sys.stdout.write("HTTP-Error: maybe the station id is incorrect\n")
        sys.exit(-1)
    except urllib.error.URLError as e:
        sys.stdout.write("URL-Error: maybe internet connection is not yet established\n")
        raise
        
    return response.read()

def get_test_file():
    fb = open(station,"rb")
    f = fb.read()
    fb.close()
    return f

def check_date(wff):
    return wff[3][0:2]

def get_description(code,config):
    """Function returns the description of the present weather in german or english."""

    if code in [str(i) for i in range(32)]:
        if config['german']:
            return(PRESENT_WEATHER_CODES[code][1])
        else:
            return(PRESENT_WEATHER_CODES[code][2])
    else:
        return "NA"

def get_values(wff,config):
    return { 
                "time" : wff[3][1] +' (UTC)', # TODO: time offset for lokal time 
                "temp" : wff[3][9] + ' °C',
                "cloud-cover" : wff[3][2]+' %',
                "visibility" : wff[3][14]+' km',
                 "maxwind" : wff[3][18]+' km/h',
                 "wind-direction" : wff[3][22]+' °',
                 "precipitation" : wff[3][33]+' mm',
                 "weather" : get_description(wff[3][35],config),
                 "pressure" : wff[3][36]+' hPa',
                 "humidity" : wff[3][37]+' %',
            }

def write_file(vals, file_path):
    s = "{} T: {}  H: {}  W: {} ({})".format(
            vals["time"],
            vals["temp"],
            vals["humidity"],
            vals["maxwind"],
            vals["weather"]
            )

    with open(file_path, "w") as f:
        f.write(s)

def write_error(err_string, file_path):
    
    with open(file_path, "w") as f:
        f.write(err_string)

def parse_args():

    config = {
            'station_file'  : None,
            'pid'           : None,
            'daemon'        : False,
            'german'        : False
            }

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--station", required=True,
            help="id of the weather station (mandatory)")
    parser.add_argument("-p", "--pid", help="path to the pid file (default {})"
            .format(PID_DEFAULT))
    parser.add_argument("-d", "--daemon", action="store_true",
            help="run as daemon (EXPERIMENTAL)")
    parser.add_argument("-g", "--german", action="store_true",
            help="display weather description in german")

    args = parser.parse_args()

    config['daemon'] = args.daemon
    config['german'] = args.german

    if args.station is None:
        sys.stderr.write("ERROR: station id needed\n")
        sys.exit(1)
    else:
        station = args.station
        if len(station) < 5:
            station +=  "_"
        config['station_file'] = station + "-BEOB.csv"

    return config

def read_weather(config):

    is_ok = True

    try:
        wf = get_file_from_url(DWD_POI_URL + config['station_file'])
        #wf = get_test_file()
    except urllib.error.URLError:
        wf = None
        is_ok = False

    if wf != None:
        wff = wf.decode("utf_8").splitlines()
        csv_reader = csv.reader(wff, delimiter=';')
        wff = [row for row in csv_reader]
        write_file(get_values(wff,config),FILE_PATH)
    else:
        write_error("service not available retrying ...",FILE_PATH)

    return is_ok

def main():
    
    config = parse_args()
    station_file_name = config['station_file']

    if os.name == 'posix':
        if os.getuid == 0 or os.geteuid == 0:
            sys.stderr.write("Do not run this script as root user!\n")
            sys.exit(1)

        if config['daemon']:
            run_as_daemon(config)
            while True:
                if read_weather(config):
                    sleep(1200)
                else:
                    while not read_weather(config):
                        sys.stderr.write("could not retrieve weather information,"
                                + " retrying ...\n")
                        sleep(60)
        else:
                read_weather(config)
    else:
        sys.stderr.write("Only for unix and compatible.\n")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
