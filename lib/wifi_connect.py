import network
import time


def do_connect(ssid, password):
    # Wait for wifi to be available.
    wlan_sta = network.WLAN(network.STA_IF)
    wlan_sta.ifconfig(('192.168.86.34', '255.255.255.0',
                       '192.168.86.1', '192.168.86.1'))
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        print('\nAlready connected. Network config: ', wlan_sta.ifconfig())
        return
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    while not wlan_sta.isconnected():
        time.sleep(0.1)
        print('.', end='')
    print('\nConnected. Network config: ', wlan_sta.ifconfig())
