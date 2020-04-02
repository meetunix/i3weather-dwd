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
import urllib.request
from time import sleep
import resource as rsc

# Quelle: Deutscher Wetterdienst
DWD_POI_URL = "https://opendata.dwd.de/weather/weather_reports/poi/"

# FILE_PATH: Path to the file where the weather information is stored.
FILE_PATH = "/tmp/i3weather-dwd"

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
    UMASK = 0o077
    REDIRECT_FD = "/dev/null"

    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
        else:
            os.setsid()
            # second fork to be sure the process is no process group leader
            pid = os.fork()
            if pid != 0:
                sys.exit(0)
            else:
                os.chdir(WORKDIR)
                os.umask(UMASK)

    except OSError as e:
        sys.stderr.write("fork  failed: {} ({})\n".format(e.errno, e.strerror))

    try: 
        # close file descriptors (may) inherited by the parent process
        max_fds = rsc.getrlimit(rsc.RLIMIT_NOFILE)[0]
        for fd in range(max_fds):
            try:
                os.close(fd)
            except OSError:
                pass
    except OSError as e:
        sys.stderr.write("closing fds failed: {} ({})\n".format(e.errno, e.strerror))

    # redirect standard file descriptor
    # get lowest descriptor name from os
    os.open(REDIRECT_FD, os.O_RDWR)
    # Duplicate standard input to standard output and standard error
    os.dup2(0, 1)
    os.dup2(0, 2)

    return 

def get_file_from_url(url):
    response = urllib.request.urlopen(url)
    #print("returned status: {} - file size: {}".
    #    format(response.status,response.getheader("Content-Length")))
    if response.status != 200:
        return None
    else:
        return response.read()

def get_test_file():
    fb = open(station,"rb")
    f = fb.read()
    fb.close()
    return f

def check_date(wff):
    return wff[3][0:2]

def get_description(code):
    """Function returns the description of the present weather in german or english."""
    if code in [str(i) for i in range(32)]:
        return(PRESENT_WEATHER_CODES[code][1])
    else:
        return "NA"

def get_values(wff):
    return { "temp" : wff[3][9] + ' °C',
             "cloud-cover" : wff[3][2]+' %',
             "visibility" : wff[3][14]+' km',
             "maxwind" : wff[3][18]+' km/h',
             "wind-direction" : wff[3][22]+' °',
             "precipitation" : wff[3][33]+' mm',
             "weather" : get_description(wff[3][35]),
             "pressure" : wff[3][36]+' hPa',
             "humidity" : wff[3][37]+' %',
            }

def write_file(vals, file_path):
    s = "{} T: {}  H: {}  W: {} ({})".format( "CURR",vals["temp"],vals["humidity"],
                     vals["maxwind"],vals["weather"])

    with open(file_path, "w") as f:
        f.write(s)

def parse_args(args):

    station = args[1]
    if len(station) < 5:
        station +=  "_"
    return station + "-BEOB.csv"

def main(station_file_name):

    wf = get_file_from_url(DWD_POI_URL + station_file_name)
    #wf = get_test_file()
    if wf != None:
        wff = wf.decode("utf_8").splitlines()
        csv_reader = csv.reader(wff, delimiter=';')
        wff = [row for row in csv_reader]
        output_value = get_values(wff)
    else:
        output_value = "NA"

    write_file(output_value,"/tmp/i3weather-dwd")
    return


def main(args):

    station_file_name = parse_args(args)

    if os.name == 'posix':
        if os.getuid == 0 or os.geteuid == 0:
            sys.stderr.write("Do not run this script as root user!")
            sys.exit(1)

        ret_val = daemonize()
        while True:
            main(station_file_name)
            sleep(1200)
    else:
        sys.stderr.write("Only for unix and compatible")
        sys.exit(1)
    
if __name__ == "__main__":
    main(sys.argv[1])
