#!/usr/bin/env python3
import urllib.request
import csv
import sys
import os
from time import sleep
import resource as rsc

# Quelle: Deutscher Wetterdienst
DWD_POI_URL = "https://opendata.dwd.de/weather/weather_reports/poi/"

#https://www.dwd.de/DE/leistungen/opendata/help/schluessel_datenformate/bufr/
#poi_present_weather_zuordnung_pdf.pdf?__blob=publicationFile&v=2
# code -> (shortDescr, detailDescr, englishDescr)
presentWeatherCodes ={  
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
        maxFD = rsc.getrlimit(rsc.RLIMIT_NOFILE)[0]
        for fd in range(maxFD):
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

def getFileFromUrl(url):
    response = urllib.request.urlopen(url)
    #print("returned status: {} - file size: {}".
    #    format(response.status,response.getheader("Content-Length")))
    if response.status != 200:
        return None
    else:
        return response.read()

def getTestFile():
    fb = open(station,"rb")
    f = fb.read()
    fb.close()
    return f

def checkDate(wff):
    return wff[3][0:2]

def getDescrFromCode(code):
    """Function returns the description of the present weather in german or english."""
    if code in [str(i) for i in range(32)]:
        return(presentWeatherCodes[code][1])
    else:
        return "NA"

def getValues(wff):
    return { "temp" : wff[3][9] + ' °C',
             "cloud-cover" : wff[3][2]+' %',
             "visibility" : wff[3][14]+' km',
             "maxwind" : wff[3][18]+' km/h',
             "wind-direction" : wff[3][22]+' °',
             "precipitation" : wff[3][33]+' mm',
             "weather" : getDescrFromCode(wff[3][35]),
             "pressure" : wff[3][36]+' hPa',
             "humidity" : wff[3][37]+' %',
            }

def writeFile(vals, filePath):
    s = "{} T: {}  H: {}  W: {} ({})".format( "CURR",vals["temp"],vals["humidity"],
                     vals["maxwind"],vals["weather"])

    with open(filePath, "w") as f:
        f.write(s)

def parseArgs():

    station = sys.argv[1]
    if len(station) < 5:
        station +=  "_"
    return station + "-BEOB.csv"

def main(statiionFileName):

    wf = getFileFromUrl(DWD_POI_URL + stationFileName)
    #wf = getTestFile()
    if wf != None:
        wff = wf.decode("utf_8").splitlines()
        csvReader = csv.reader(wff, delimiter=';')
        wff = [row for row in csvReader]
        outValue = getValues(wff)
    else:
        outValue = "NA"

    writeFile(outValue,"/tmp/i3weather-dwd")
    return

stationFileName = parseArgs()

if os.name == 'posix':
    if os.getuid == 0 or os.geteuid == 0:
        sys.stderr.write("Do not run this script as root user!")
        sys.exit(1)

    retVal = daemonize()
    while True:
        main(stationFileName)
        sleep(1200)
else:
    sys.stderr.write("Only for unix and compatible")
    sys.exit(1)
    
