# noinspection PyPackageRequirements
import serial
import time
import datetime
from urllib.request import urlopen
import json
import os
import hashlib
from whitelist_handler import Whitelist


def read_last_line(ser, whitelist: Whitelist) -> dict:
    """
    Reads the last line from the serial port (ser) and return the data as a dictionary.

    :param ser: The serial connection
    :param whitelist: A list of known mac-addresses. If the mac address is not in this list, name is returned as False.
    :return: A dictionary with mac, rssi, time, name
    :rtype: dict
    """

    try:
        # Read the line and split it
        data = ser.readline().decode()[:-2].split(',')
        mac = data[1]

        # Check whether the second to last binary digit of the first byte is 0
        # If it is 1 it is a spoofed address
        if int(mac[:2], base=16) / 2 % 2 < 1:

            # If the mac adress is not in the whitelist, use a hash instead
            if not whitelist.macs.get(mac, False):
                h = hashlib.sha256('hoax'.encode('utf-8'))
                h.update(mac.encode('utf-8'))
                datadict = {'mac': h.hexdigest()[:16], 'time': time.time(), 'id': -1}
            else:
                datadict = {'mac': mac, 'time': time.time(), 'id': whitelist.macs.get(mac)}
        else:
            return dict()
    except AttributeError:
        print('Warning, no serial data found')
        return dict()
    except IndexError:
        return dict()
    except ValueError:
        return dict()
    else:
        return datadict


def update(array: dict, last_line: dict) -> dict:
    """
    Preforms several checks whether the currentmost data from the serial connection is valid.
    If this is the case, it adds this entry to the array of present mac-addresses.

    :param array: The array of present mac-addresses
    :param last_line: The last line read from the serial connection
    :return: The array of present mac-addresses
    :rtype: dict
    """

    # Storing this first gives a slight performance increase
    mac = last_line['mac']
    # print(mac)
    # Check whether an entry exists for this mac-address.
    # If not, add an empty entry for this mac-address.
    # Otherwise, make sure the last known timestamp is more than one second old.
    if mac not in array:
        array[mac] = {'times': [], 'id': last_line['id']}
    elif last_line['time'] - array[mac]['times'][-1] < 1:
        return array

    # Add the timestamp to the entry.
    array[mac]['times'].append(last_line['time'])

    return array


def pop_timed_out(array: dict, t: float) -> dict:
    """
    Check wether a timestamp in any of the entries is too old. If so, it is popped from data.
    If this results in an entry without data, the entry is removed.

    :param array: The array of present mac-addresses
    :param t: The time with which to compare the timestamps.
    :return: The array that whas provided, minus all popped timestamps.
    :rtype: dict
    """
    for entry in list(array):
        for i, d in enumerate(array[entry]['times']):
            if t - d > 300:
                array[entry]['times'].pop(i)

        if not array[entry]['times']:
            del array[entry]

    return array


def save_present(array: dict, t: float):
    """
    Splits the array of present mac-addresses by known/unknown and adds a line to their respecive log files.
    Also sends the list of present-known to the online overview using json
    :param array: The array of present mac-addresses
    :param t: The time of saving the data.
    """
    pr_known = []
    pr_unknown = []
    pr_web = []
    for entry in array:
        if array[entry]['id'] != -1:
            pr_known.append(entry)
            pr_web.append(array[entry]['id'])
        else:
            pr_unknown.append(entry)

    pr_known.append(str(t))
    pr_unknown.append(str(t))
    pr_web.append(str(datetime.datetime.fromtimestamp(t)))

    json_string = json.dumps(pr_web)
    url = ('https://www.borrelcie.vodka/present?data=' + json_string).replace(' ', '')
    print('Uploading: ' + url)

    try:
        # pass
        urlopen(url)
    except OSError:
        print('URLError')
    else:
        pass
        # print('URLWin')

    dr = os.path.dirname(__file__)

    present_file = os.path.join(dr, 'present/present')
    with open(present_file, 'a') as present:
        present.write(str(pr_known) + '\n')
    print('Nu zijn er:', pr_known)

    unknown_file = os.path.join(dr, 'present/unknown_hash')
    with open(unknown_file, 'a') as present:
        present.write(str(pr_unknown) + '\n')
    print('De onbekenden:', pr_unknown)


def main():
    t = time.time()

    whitelist = Whitelist()
    whitelist.update()

    # Establish the serial connection and reset the line.
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    # from fake_serial import FakeSerial
    # ser = FakeSerial()

    ser.setDTR(False)
    time.sleep(1)
    ser.setDTR(True)
    # This resets the data-terminal-ready line

    array = dict()
    save_pr_time = t
    check_wl_time = t

    while True:

        # Synchronize all times
        t = time.time()

        # Read the last line from the serial port.
        last_line = read_last_line(ser, whitelist)

        # Check whether a last line was returned, if not sleep for a while.
        if last_line:
            array = update(array, last_line)

        # Save the list of present mac-addresses every five seconds
        if t - save_pr_time > 5:
            array = pop_timed_out(array, t)

            save_present(array, t)
            save_pr_time = t

        # Check whitelist every 30 minutes
        if t - check_wl_time > 1800:
            whitelist.update()
            whitelist.get_macs_by_id(2)
            check_wl_time = t


if __name__ == '__main__':
    main()
