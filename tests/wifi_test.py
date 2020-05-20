import network
from wifi_connect import do_connect

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.disconnect()
do_connect("happyday", "poi098lkj")
