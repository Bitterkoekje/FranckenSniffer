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
from matplotlib.pyplot import cm
import matplotlib.ticker as ticker
import matplotlib.patheffects as pe
import matplotlib.image as image
import itertools


def read_data(whitelist: Whitelist, dt_min: datetime, dt_max: datetime,
              cluster: datetime.timedelta = datetime.timedelta(minutes=20)):
    """
    Import names and timestamps from the present-logfile and return them as a dict with id:datetimes entries.
    :param whitelist: List of known mac:name combinations
    :param dt_min:  Minimum datetime
    :param dt_max:  Maximum datetime
    :param cluster: Datapoints closer together than cluster will be combined into a line
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
            if dt_min <= dt <= dt_max and not (datetime.time(0, 0) < dt.time() < datetime.time(8, 0)):

                # Go through all present names and make sure they are in the whitelist
                for mac in data[:-1]:
                    if mac in whitelist.macs:
                        id_ = whitelist.macs[mac]

                        # If there is no entry for this name in the present dict, make one.
                        if id_ not in present:
                            present[id_] = []

                        present[id_].append(dt)

    # pprint.pprint(present)
    lines = dict()
    for i in present:
        lines[i] = list()
        # print(i)
        dt_previous = dt_min
        dt_start = dt_min
        dt_end = dt_max
        l = len(present[i])
        for j, dt_current in enumerate(present[i]):
            if j == 0:
                dt_start = dt_current
            elif dt_current - cluster > dt_previous:
                dt_end = dt_previous
                lines[i].append([dt_start, dt_end])
                # print(i, whitelist.names[i]['name'], dt_start, dt_end, dt_end - dt_start)
                dt_start = dt_current
            elif j == l-1:
                dt_end = dt_current
                lines[i].append([dt_start, dt_end])
                # print(i, whitelist.names[i]['name'], dt_start, dt_end, dt_end - dt_start, 'last')
            dt_previous = dt_current
    return lines


def saveplot(present: dict, whitelist: Whitelist, dt_min: datetime, dt_max: datetime, strict_xlim: bool = True):
    """
    Save a plot of present names
    :param whitelist:   Whitelist from whitelist_handler
    :param present:     Dict of name:datetimes entries
    :param dt_min:      Minimum datetime
    :param dt_max:      Maximum datetime
    :param strict_xlim:
    """

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), gridspec_kw={'height_ratios': [6, 1]})
    plt.subplots_adjust(bottom=0.05, top=0.95, hspace=0.15)
    # ax1.spines["top"].set_visible(False)
    # ax1.spines["right"].set_visible(False)
    # plt.title(dt_min.strftime('%d-%m-%Y %H:%M') + ' - ' + dt_max.strftime('%d-%m-%Y %H:%M'))

    # Configure the x-axis such that it takes dates.
    # fig.autofmt_xdate()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator())

    # if dt_max - dt_min <= datetime.timedelta(hours=4):
    #     ax1.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 15, 30, 45]))
    #
    # elif dt_max - dt_min <= datetime.timedelta(hours=24):
    #     ax1.xaxis.set_major_locator(mdates.HourLocator())
    #
    # else:
    #
    #     plt.gcf().autofmt_xdate(rotation=30, ha='center')
    #     ax1.xaxis.set_major_locator(mdates.DayLocator())
    #     ax1.xaxis.set_minor_locator(mdates.HourLocator(byhour=12))
    #     ax1.xaxis.set_major_formatter(ticker.NullFormatter())
    #     ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%A\n%d-%m-%y'))
    # plt.gca().xaxis.set_major_locator(mdates.HourLocator())

    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')

    # For each name, plot its datetimes.
    # Each name get's a unique y coordinate.
    color = itertools.cycle(cm.tab10(np.linspace(0, 1, cm.tab10.N)))

    for i, id_ in enumerate(present):
        path_effects = []
        if 'color' in whitelist.names[id_]:
            c = whitelist.names[id_]['color']
        else:
            c = next(color)
        y = [i+1, i+1]

        lw = 15

        if 'outline' in whitelist.names[id_]:
            path_effects.append(pe.withStroke(linewidth=lw, foreground='k'))
            lw -= 3

        for a in present[id_]:
            # print(id_, a)
            ax1.plot(a, y, markersize=8, linewidth=lw, solid_capstyle='round', color=c, path_effects=path_effects)

    # Use the names as yticks
    ax1.set_yticks(range(1, len(present) + 1))
    ax1.set_yticklabels([whitelist.names[id_]['name'] for id_ in present])

    if strict_xlim or not present:
        ax1.set_xlim(dt_min, dt_max)

    ax1.set_ylim(0, len(present) + 1)

    ax1.grid()

    if not present:
        print('NO DATA')
        fig.text(0.5, 0.5, 'NO DATA', size=50, ha="center", va="bottom", color='#aaaaaa', weight='bold')

    ax2.text(-100, 250, 'Sponsored by', size=20, ha="right", va="bottom", color='#68686d', weight='bold')
    im = image.imread('nedap.png')
    ax2.axis('off')
    ax2.imshow(im)
    # size = fig.get_size_inches()*300
    # # plt.imshow(im, aspect='auto', zorder=-1)
    # print(size)
    # ax.figure.figimage(im, size[0]*0.5, 100, zorder=1)
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
        dt_now = datetime.datetime.now()
        # dt_max = datetime.datetime(2018, 6, 29, 0, 0, 0)
        dt_min = datetime.datetime.combine(dt_now.date(), datetime.time(8, 0))
        # dt_max = datetime.datetime.combine(dt_now.date(), datetime.time(23, 59))
        dt_max = dt_now
        # dt_min = dt_max - datetime.timedelta(hours=12)

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
