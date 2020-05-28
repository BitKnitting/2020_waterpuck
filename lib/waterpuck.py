#
# In the 2020 version of the waterpuck,

import json
import usocket as socket
from wifi_connect import do_connect
from machine import Pin
from minute_timer import MinuteTimer
# See info about const here https://www.youtube.com/watch?v=hHec4qL00x0&t=656s
from micropython import const

WLAN_PROFILE = 'lib/wifi.dat'
VALVES_JSON = 'lib/valves.json'
CONTENT_PREAMBLE = b"HTTP/1.0 200 OK \n\n   "
WATERING_MINS = const(1)  # The number of minutes to keep each valve open.
MIN_WATERING_TIME = const(1)
MAX_WATERING_TIME = const(30)


class WaterPuck:
    def __init__(self):
        # Get the pins from the valves file.
        with open(VALVES_JSON) as f:
            self.valves_dict = json.load(f)
        # set to a "default" pin.
        self.watering_pin = Pin(0, Pin.OUT)
        self.valve_key = ""
        self.watering_mins = WATERING_MINS

        # Initialize the minute timer with the number of watering minutes
        # for each valve as well as the callback function when the timer
        # goes off.  The timer starts when the start_timer() method is invoked.
        self.minute_timer = MinuteTimer(
            self._turn_off_valve, self.watering_mins)
        # Get the wifi's password and ssid.
        with open(WLAN_PROFILE) as f:
            line = f.readline()
        self.ssid, self.password = line.strip("\n").split(";")
        print("ssid: {}. password: {}".format(self.ssid, self.password))

    #########################################################
    # Listen calls _send_response to let the web client know
    # it received a request.
    #########################################################

    def _send_response(self, conn, specific):
        content = CONTENT_PREAMBLE + bytes(specific, 'utf-8')
        conn.sendall(content)
    #########################################################
    # _turn_off_valve gets called by the callback when
    # the watering time has completed as well as when
    # Listen receives the water_off command.
    #########################################################

    def _turn_off_valve(self):
        self.watering_pin.off()
        print('turned off valve {} on pin {}.'.format(
            self.valve_key, self.watering_pin))
        # Cycle to the next valve.
        self.valves_dict.pop(self.valve_key)

        self._cycle_through_valves()

    #########################################################

    #########################################################

    def _cycle_through_valves(self):
        if len(self.valves_dict) != 0:
            valve_keys = self.valves_dict.keys()
            key_iterator = iter(valve_keys)
            self.valve_key = next(key_iterator)
            self.watering_pin = Pin(self.valves_dict[self.valve_key], Pin.OUT)
            self.watering_pin.on()
            print('turned on valve pin {}'.format(
                self.valves_dict[self.valve_key]))
            self.minute_timer.start_timer()

    #########################################################
    def _get_input(self, request_str):
        equal_sign = request_str.find('=')
        return request_str[equal_sign+1:].split()[0]
    #########################################################

    def _remove_valve(self, request_str):
        key = self._get_input(request_str)
        print('in _is_remove_valve.  Key to remove: {}'.format(key))
        if key in self.valves_dict.keys():
            self.valves_dict.pop(key)
        return key
    #########################################################

    def _get_valve_str(self):
        str = ""
        for k, v in self.valves_dict.items():
            valve_str = ' the {} valve on pin {}   '.format(k, v)
            str += valve_str
        return str

    #########################################################

    def _set_watering_time(self, request_str):
        x = self._get_input(request_str)
        try:
            watering_mins = int(x)
        except ValueError:
            return False
        if watering_mins > MAX_WATERING_TIME or watering_mins < MIN_WATERING_TIME:
            return False
        self.watering_mins = watering_mins
        return True

    #########################################################
    # Listen is the main method called after initialization.  This
    # function creates a web server and then listens for the
    # stop and start (watering) html commands.  I've been
    # using Angry IP to figure out what IP address to connect
    # to.
    #
    #########################################################

    def listen(self, port):
        do_connect(self.ssid, self.password)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen(1)
        counter = 0
        while True:
            conn, addr = s.accept()
            print('Got connection #{} from {}' .format(counter, addr))
            counter += 1
            request = conn.recv(1024)
            request = str(request)
            # Figure out if the URL is for controlling valve(s)
            start_watering = request.find('water_on')
            stop_watering = request.find('water_off')
            valve_off = request.find('valve_off')
            exit_listen = request.find('exit')
            watering_time = request.find('water_time')
            hello_listen = request.find('hello')
            # The check is a follow up to the request.find()...
            if (hello_listen != -1 and hello_listen < 10):
                # Command sent to start watering.
                valve_str = self._get_valve_str()
                min_str = "minute" if self.watering_mins == 1 else "minutes"
                return_str = 'Hello - the watering time is set to {} {}. \n   Valves: {}.'.format(
                    self.watering_mins, min_str, valve_str)
                self._send_response(conn, return_str)

            if (start_watering != -1 and start_watering < 10):
                # Command sent to start watering.
                self._send_response(conn, 'start watering')
                self._cycle_through_valves()

            elif (stop_watering != -1 and stop_watering < 10):

                # Command sent to stop watering.
                self._send_response(conn, 'stop watering')
                # THere's only one valve on at a time.
                self._turn_off_valve()
            elif (valve_off != -1 and valve_off < 10):
                # See if the valve string is in the dictionary of valves.
                return_str = ""
                key = self._remove_valve(request[valve_off:])
                if len(key) != 0:
                    return_str = "Will not turn the water on for the {} valve ".format(
                        key)
                else:
                    return_str = "Not a valid valve name."
                valve_str = self._get_valve_str()
                return_str += '\n   Valves that are on include {}'.format(
                    valve_str)
                self._send_response(conn, return_str)
            elif (watering_time != -1 and watering_time < 10):
                # The first part of the request has been truncated.  I send
                # the request string at the location where the string
                # water_time starts.
                is_watering_time_set = self._set_watering_time(
                    request[watering_time:])
                return_str = ""
                if (is_watering_time_set):
                    min_str = "minute" if self.watering_mins == 1 else "minutes"
                    return_str = "Changing the watering time to {} {}.".format(
                        self.watering_mins, min_str)
                else:
                    return_str = "The watering time must be between {} minutes and {} minutes.   The watering time is still {} minutes.".format(MIN_WATERING_TIME, MAX_WATERING_TIME,
                                                                                                                                                self.watering_mins)
                self._send_response(conn, return_str)
            elif (exit_listen != -1 and exit_listen < 10):
                self._turn_off_valve()
                conn.close()
                print('received a request to exit, buh-bye')
                break
            else:
                print('received packet.  Was not a water request')
            conn.close()
        s.close()
