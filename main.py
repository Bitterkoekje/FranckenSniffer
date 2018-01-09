# noinspection PyPackageRequirements
import serial
import time
from urllib.request import urlopen
import json
import os


def read_last_line(ser, whitelist: dict) -> dict:
    """
    Reads the last line from the serial port (ser) and return the data as a dictionary.

    :param ser: The serial connection
    :param whitelist: A list of known mac-addresses. If the mac address is not in this list, name is returned as False.
    :return: A dictionary with mac, rssi, time, name
    :rtype: dict
    """

    # THIS IS A DUMMY LAST_LINE FOR DEBUGGING!
    # ---------------------------------------
    # macs = ['2c:f0:a2:d8:2e:bf', '2c:f0:23:d8:df:af', 'c0:ee:fb:42:91:99']
    # data = [np.random.randint(-85, -60), np.random.choice(list(whitelist))]
    # data = [np.random.randint(-85, -60), np.random.choice(macs)]
    # data = []
    # ---------------------------------------

    try:
        data = ser.readline().decode()[:-2].split(',')
    except AttributeError:
        print('Warning, no serial data found')
        return dict()
    else:
        return {'mac': data[1], 'rssi': 100 + int(data[0]), 'time': time.time(), 'name': whitelist.get(data[1], False)}


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
    
    # Check whether an entry exists for this mac-address.
    # If not, add an empty entry for this mac-address.
    # Otherwise, make sure the last known timestamp is more than one second old.
    if mac not in array:
        array[mac] = {'data': [], 'name': last_line['name']}
    elif last_line['time'] - array[mac]['data'][-1]['time'] < 1:
        return array

    # Add the timestamp to the entry.
    array[mac]['data'].append({'time': last_line['time'], 'rssi': last_line['rssi']})

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
        for i, d in enumerate(array[entry]['data']):
            if t - d['time'] > 300:
                array[entry]['data'].pop(i)

        if not array[entry]['data']:
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
    for entry in list(array):
        if array[entry]['name']:
            pr_known.append(array[entry]['name'])
        else:
            pr_unknown.append(entry)

    pr_known.append(str(t))
    pr_unknown.append(str(t))

    json_string = json.dumps(pr_known)
    url = ('https://www.borrelcie.vodka/present?data=' + json_string).replace(' ', '')
    print('Uploading: ' + url)
    urlopen(url)

    dir = os.path.dirname(__file__)

    present_file = os.path.join(dir, 'present/present')
    with open(present_file, 'a') as present:
        present.write(str(pr_known) + '\n')
    print('Nu zijn er:', pr_known)

    unknown_file = os.path.join(dir, 'present/unknown')
    with open(unknown_file, 'a') as present:
        present.write(str(pr_unknown) + '\n')
    print('De onbekenden:', pr_unknown)


def check_whitelist() -> dict:
    """
    Import the whitelist of mac-addresses and return it as a dict.
    :return: whitelist
    :rtype: dict
    """

    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, 'whitelists/whitelist')
    with open(filename) as text:
        whitelist = eval(text.read())
    return whitelist


def main():
    t = time.time()
    whitelist = check_whitelist()
    ser = serial.Serial('/dev/ttyUSB0', 115200)

    array = dict()
    save_pr_time = t
    check_wl_time = t
    while True:
        t = time.time()
        last_line = read_last_line(ser, whitelist)
        if not last_line:
            time.sleep(10)
        else:
            array = update(array, last_line)

        # Save the list of present mac-addresses every two seconds
        if t - save_pr_time > 2:
            array = pop_timed_out(array, t)
            save_present(array, t)
            save_pr_time = t

        # Check whitelist every 30 minutes
        if t - check_wl_time > 3600:
            whitelist = check_whitelist()
            check_wl_time = t


if __name__ == '__main__':
    main()
