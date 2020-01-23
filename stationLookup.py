#!/usr/bin/env python3
import urllib.request
import re
import sys

# Quelle: Deutscher Wetterdienst
allStationsUrl = 'https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication&nn=16102'
availableStationsUrl = 'https://opendata.dwd.de/weather/weather_reports/poi/'

def getFileFromUrl(url):
    response = urllib.request.urlopen(url)
    #print("returned status: {} - file size: {}".
    #    format(response.status,response.getheader("Content-Length")))
    if response.status != 200:
        return None
    else:
        return response.read()
    
def getTestFile(path):
    fb = open(path,"rb")
    f = fb.read()
    fb.close()
    return f

def buildStationsDict(statList, availStatList):
    stationsDict = {}
    for l in statList:
        if re.match('^9',l):
            l = l[12:]
            sId = l.split(' ')[0]
            if sId in availStatList:
                place = l[11:32].strip().lower() 
                stationsDict.update({sId : place})
    return stationsDict

def buildAvailStationsList(ll):
    availableStations = []
    for l in ll:
        if re.match('^<a href',l):
            l = l.split("\"")
            l = l[1].split("-")[0].replace("_"," ").strip()
            availableStations.append(l)
    return availableStations

def main(search):
    
    availStations = getFileFromUrl(availableStationsUrl)
    availStations = availStations.decode('utf_8').splitlines()
    availStations = buildAvailStationsList(availStations)

    stations = getFileFromUrl(allStationsUrl)
    #stations = getTestFile('mosmix_stationskatalog.cfg') 
    stations = stations.decode("iso8859-1").splitlines()
    stationsDict = buildStationsDict(stations, availStations)

    search = search.strip().lower()
    pattern = '.*'+search+'.*'
    pattern = re.compile(pattern)
    for key, place in stationsDict.items():
        if re.match(pattern,place):
            print("{:5} <--> {}".format(key,place))

main(sys.argv[1])



