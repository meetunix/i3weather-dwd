# i3weather-dwd

i3status plugin for displaying weather information from the German Meteorological
Service (Deutscher Wetterdienst). 

The DWD (Deutscher Wetterdienst) publishes most of its data on its
[open data platform](https://www.dwd.de/DE/leistungen/opendata/opendata.html).

In fact `i3weather-dwd` isn't a plugin, but it uses the `read_file` module from i3status.
`i3weather-dwd` creates and updates the file `/tmp/i3weather-dwd` regularly and the
`read_file` module will read the file on change.

`i3weather-dwd` could run as a **daemon** or may be invoked by **cron**.

The Information is displayed in the following manner:

    T: 6,5 °C  H: 78 %  W: 28 km/h (bedeckt)

or in english:

    T: 6,5 °C  H: 78 %  W: 28 km/h (overcast)




T: temperature in degree celsius (2 meter above surface). 

H: relative air humidity.

W: average wind speed last hour.

(meterological description)


## installation

Clone the repository an make sure you have `python3 >= 3.5` and `i3status >= 2.13` installed.


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
searching a generated snapshot of the weather stations in [stations.md](stations.md).


Using the live lookup is very easy. If there is no station in your town, maybe there is
one in the neighbouring town.

    i3weather-dwd/stationLookup.py rostock
    no station found
    
    i3weather-dwd/stationLookup.py warnemünde
    10170 <--> warnemuende

The station id for the weather station located in Warnemünde is 10170.


### running i3weather-dwd once or with cron 

If you want to start the `i3weather-dwd` a single time, just run it.

    /usr/local/bin/i3weather-dwd.py -s STATION-ID


Maybe you want to use cron for regulary updates

    */20 * * * *    /usr/local/bin/i3weather-dwd.py -s STATION-ID

That means: every 20 minutes an update is performed.



### updating your i3status.conf

Simply add the following lines to your config (mostly `~/.i3status.conf`) and reload i3.

    order += "read_file weather"

    ...


    read_file weather {
        format = %content
        path = "/tmp/i3weather-dwd"
    }


### command line options
    
    # mandatory

    -s --station    STRING      Station-ID

    # optional

    -d --daemon     FLAG        run as daemon (experimental)
    -p --pid        STRING      alternate path to the pid

    -g --german     FLAG        meterological description is displayed in german

### running as a daemon (experimental)

You are able to run `i3weather-dwd` as a daemon. The prefered way is the use
of **systemd**. But you can also start it like this:

    /usr/local/bin/i3weather-dwd.py -s STATION-ID -d
    

#### using systemd

Copy the following [file](contrib/i3weather-dwd.service) to
`/etc/systemd/system/i3weather-dwd.service` and change the user and group names under
which the service has to be started.

    [Unit]
    Description=i3weather-dwd

    [Service]
    User=USERNAME
    Group=GROUPNAME
    Type=forking
    ExecStart=/usr/local/bin/i3weather-dwd.py -s 10170 -d
    PIDFile=/tmp/i3weather-dwd.pid
    TimeoutStartSec=5

    [Install]
    WantedBy=multi-user.target

Then start and enable the service.


    sudo systemctl daemon-reload
    
    sudo systemctl start i3weather-dwd.service
    
    sudo systemctl enable i3weather-dwd.service

Have fun!
