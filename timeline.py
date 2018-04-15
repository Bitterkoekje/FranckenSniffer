import numpy as np
import time
import datetime
import re
import matplotlib
import os
from shutil import copy2
from whitelist_handler import Whitelist

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


def read_data(whitelist: Whitelist, dt_min: datetime, dt_max: datetime):
    """
    Import names and timestamps from the present-logfile and return them as a dict with id:datetimes entries.
    :param whitelist: List of known mac:name combinations
    :param dt_min:  Minimum datetime
    :param dt_max:  Maximum datetime
    :return: present
    :rtype: dict
    """
    # Get the data from the present-logfile.
    # For performace reasons, only the last part of the file is loaded. This only works on UNIX.
    dr = os.path.dirname(__file__)
    filename = os.path.join(dr, 'present/present')
    with os.popen('tail -n 100000 ' + filename) as f:
        file = f.read()

    present = dict()

    # Split the data from present by line
    for line in file.splitlines():
        # Extract the data from the line, the last element is always the timestamp
        data = re.findall(r"[' ]([\w\d].*?)['\]]", line)

        # Make sure the line is not only a timestamp
        if len(data) > 1:

            # Make sure the timestamp is in the specified range
            dt = datetime.datetime.fromtimestamp(float(data[-1]))
            if dt_min <= dt <= dt_max:

                # Go through all present names and make sure they are in the whitelist
                for mac in data[:-1]:
                    if mac in whitelist.macs:
                        id_ = whitelist.macs[mac]

                        # If there is no entry for this name in the present dict, make one.
                        if id_ not in present:
                            present[id_] = []

                        present[id_].append(dt)

    return present


def saveplot(present: dict, whitelist: Whitelist, dt_min: datetime, dt_max: datetime, strict_xlim: bool = True):
    """
    Save a plot of present names
    :param whitelist:   Whitelist from whitelist_handler
    :param present:     Dict of name:datetimes entries
    :param dt_min:      Minimum datetime
    :param dt_max:      Maximum datetime
    :param strict_xlim:
    """

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.title(dt_min.strftime('%d-%m-%Y %H:%M') + ' - ' + dt_max.strftime('%d-%m-%Y %H:%M'))

    # Configure the x-axis such that it takes dates.
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    if dt_max - dt_min <= datetime.timedelta(hours=4):
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 15, 30, 45]))

    elif dt_max - dt_min <= datetime.timedelta(hours=24):
        plt.gca().xaxis.set_major_locator(mdates.HourLocator())

    else:

        plt.gcf().autofmt_xdate(rotation=30, ha='center')
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.gca().xaxis.set_minor_locator(mdates.HourLocator(byhour=12))
        plt.gca().xaxis.set_major_formatter(ticker.NullFormatter())
        plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('%A\n%d-%m-%y'))

    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    # For each name, plot its datetimes.
    # Each name get's a unique y coordinate.
    for i, id_ in enumerate(present):
        y = np.ones(len(present[id_])) * (i + 1)
        print(whitelist.names[id_]['buixieval'])
        if whitelist.names[id_]['buixieval'] == 'pink' or whitelist.names[id_]['buixieval'] == 'c_pink':
            c = '#ff99ff'
        elif whitelist.names[id_]['buixieval'] == 'blue' or whitelist.names[id_]['buixieval'] == 'c_blue':
            c = '#01ffff'
        else:
            c = '#dddddd'
        ax.plot(present[id_], y, 's', markersize=8, color=c)

    # Use the names as yticks
    plt.yticks(range(1, len(present) + 1), [whitelist.names[id_]['name'] for id_ in present])

    if strict_xlim or not present:
        plt.xlim(dt_min, dt_max)

    plt.ylim(0, len(present) + 1)

    plt.grid()
    plt.savefig('slide_tmp.png', dpi=300)
    plt.close('all')
    
    print('Moving file')
    copy2('slide_tmp.png', 'slide.png')
    return


def main():
    # Import the whitelist
    whitelist = Whitelist(filters={'screen': True})

    while True:
        whitelist.update()
        # Set the begin and end datetimes to the last twelve hours
        dt_max = datetime.datetime(2018, 4, 7)
        dt_min = dt_max - datetime.timedelta(hours=12)

        t = time.time()

        # Import the present-data
        present = read_data(whitelist, dt_min, dt_max)

        # Save the plot
        saveplot(present, whitelist, dt_min, dt_max, False)

        print('Plot saved for dates between ' + str(dt_min) + ' and ' + str(dt_max) + ' for ' + str(len(present)) +
              ' names in ' + str(time.time() - t) + ' seconds.')

        time.sleep(10)


if __name__ == '__main__':
    main()
