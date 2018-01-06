import numpy as np
import time
import datetime
import re
import matplotlib
import os

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


def check_schermwhitelist() -> dict:
    """
    Import the whitelist of mac-addresses and return it as a dict.
    :return: whitelist
    :rtype: dict
    """

    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, 'whitelists/schermwhitelist')
    with open(filename) as text:
        whitelist = eval(text.read())
    return whitelist


def read_data(dt_min: datetime, dt_max: datetime):
    """
    Import names and timestamps from the present-logfile and return them as a dict with name:datetimes entries.
    :param dt_min:  Minimum datetime
    :param dt_max:  Maximum datetime
    :return: present
    :rtype: dict
    """
    # Get the data from the present-logfile.
    # For performace reasons, only the last part of the file is loaded. This only works on UNIX.
    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, 'present/present')
    with os.popen('tail -n 100000 ' + filename) as f:
        file = f.read()

    # Import the whitelist
    whitelist = check_schermwhitelist()

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
                for name in data[:-1]:
                    if name in whitelist.values():

                        # If there is no entry for this name in the present dict, make one.
                        if name not in present:
                            present[name] = []

                        present[name].append(dt)

    return present


def saveplot(present: dict, dt_min: datetime, dt_max: datetime, strict_xlim: bool = True):
    """
    Save a plot of present names
    :param present:     Dict of name:datetimes entries
    :param dt_min:      Minimum datetime
    :param dt_max:      Maximum datetime
    :param strict_xlim:
    """

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.title(str(dt_min) + ' - ' + str(dt_max))

    # Configure the x-axis such that it takes dates.
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%y   %H:%M'))

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
    for i, name in enumerate(present):
        y = np.ones(len(present[name])) * (i + 1)
        ax.plot(present[name], y, 's', markersize=8)

        # Place the name at the first datetime
        # plt.text(min(present[name]), i+1.3, name)

    # Use the names as yticks
    plt.yticks(range(1, len(present) + 1), present)

    if strict_xlim or not present:
        plt.xlim(dt_min, dt_max)

    plt.ylim(0, len(present) + 1)

    plt.grid()
    plt.savefig('slide.png', dpi=300)
    plt.close('all')
    return


def main():
    while True:
        dt_max = datetime.datetime.now()
        dt_min = dt_max - datetime.timedelta(hours=12)

        t = time.time()
        present = read_data(dt_min, dt_max)
        saveplot(present, dt_min, dt_max, True)

        print('Plot saved for dates between ' + str(dt_min) + ' and ' + str(dt_max) + ' for ' + str(len(present)) +
              ' names in ' + str(time.time() - t) + ' seconds.')

        time.sleep(10*60)


if __name__ == '__main__':
    main()
