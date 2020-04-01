# i3weather-dwd

i3status plugin for displaying weather information from the German Meteorological
Service (Deutscher Wetterdienst). 

The DWD (Deutscher Wetterdienst) publishes most of its data on its
[open data platform](https://www.dwd.de/DE/leistungen/opendata/opendata.html).

In fact it isn't a plugin, but it uses the `read_file` module from i3status.
`i3weather-dwd` creates and updates the file `/tmp/i3weather-dwd` regularly and the
`read_file` module will read the file on change.

`i3weather-dwd` runs as a daemon an may be controlled by systemd.

The Information is displayed in the following manner:

    T: 6,5 °C  H: 78 %  W: 28 km/h (bedeckt)

or in english:

    T: 6,5 °C  H: 78 %  W: 28 km/h (overcast)




T: temperature in degree celsiusn 2 meter above surface. 

H: relative air humidity.

W: average wind speed last hour.

(meterological description)


## installation

Clone the repository an make sure you have `python3 >= 3.4` and `i3status >= 2.13` installed.


    i3status -v
    i3status 2.13 © 2008 Michael Stapelberg and contributors
    
    python3 --version
    Python 3.8.2

    git clone --depth=1 https://github.com/meetunix/i3weather-dwd.git


Copy the executable (python script) to a location of your choice.


    cp i3weather-dwd/i3weather-dwd.py /usr/local/bin/


## configuration

### weather station lookup

Every weather station has a unique id. You need to find out this number to use
`i3weather-dwd`. A weather station located in germany is updated **hourly**. You will
find the same information on their
[website](https://www.dwd.de/DE/wetter/wetterundklima_vorort/mecklenburg-vorpommern/warnemuende/_node.html).


You have the choice beetween a live lookup using the `station-lookup.py` script, or
searching a generated snapshot of the weather stations in (stations.md)[stations.md].


Using the live lookup is very easy. If there is no station in your town, maybe there is
one in the neighbouring town.

    i3weather-dwd/stationLookup.py rostock
    no station found
    
    i3weather-dwd/stationLookup.py warnemünde
    10170 <--> warnemuende

The station id for the weather station located in Warnemünde is 10170.


### start without systemd

If you want to start the `i3weather-dwd` daemon without systemd, just run it.

    /usr/local/bin/i3weather-dwd.py STATION-ID

Per default a pid-file is written to `/run/i3weather-dwd`. 


### create a systemd unit file

...

### updating your i3status.conf

Simply add the following lines to your config (mostly `~/.i3status.conf`) and reload i3.

    order += "read_file weather"

    ...


    read_file weather {
        format = %content
        path = "/tmp/i3weather-dwd"
    }

It is done, `i3weather-dwd` will look every 20 minutes for changes.


### command line options
    
    # mandatory

    -s      Integer     Station-ID

    # optional

    -p      PATH        alternate path to the pid
    -g                  flag, meterological description is displayed in german

