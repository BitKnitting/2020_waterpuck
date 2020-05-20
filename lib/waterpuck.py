

import network
import usocket as socket
from wifi_connect import do_connect
from machine import Timer, Pin

WLAN_PROFILE = 'lib/wifi.dat'
CONTENT_PREAMBLE = b"HTTP/1.0 200 OK \n\n   "
WATERING_TIME = 1  # The number of minutes to keep the valve open.
# KLUDGE - i couldn't get the wemos to callback if the period between callbacks was
# > 7 minutes.  So Make the WATERING_TIME in increments of 5, with 5 being the lowest
# amount of time.


class WaterPuck:
    def __init__(self, *tuple_of_gpio_pins_for_valves):
        self.pins_set_to_valves = tuple_of_gpio_pins_for_valves
        print('pins: {}'.format(self.pins_set_to_valves))
        # set to a "default" pin.
        self.watering_pin = Pin(0, Pin.OUT)
        self.tim = Timer(-1)
        self.num_five_min_callbacks = WATERING_TIME/5
        self.num_five_min_called_back = 0
        # self.watering_ms = 5 * 60 * 1000  # Watering increments is in 5 minutes
        self.watering_ms = 60 * 5 * 100
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
        self.tim.deinit()
        self.watering_pin.off()
        self.bStopped_watering = True
        print('turned off valve on pin {}.'.format(self.watering_pin))
        self.watering_pin.off()
    #########################################################
    # _turn_on_valve_and_wait sets up this callback to happen
    # after the watering time has completed.  It then turns
    # the valve off and calls _turn_on_valve_and_wait to start
    # turn on the next valve.
    #########################################################

    def _watering_callback(self, valve_pin_list):
        self.num_five_min_called_back += 1
        print('in callback.  Num times called back: {} num callbacks will happen: {}'.format(
            self.num_five_min_called_back, self.num_five_min_callbacks))
        if (self.num_five_min_called_back < self.num_five_min_callbacks):
            self.tim.init(period=self.watering_ms, mode=Timer.ONE_SHOT,
                          callback=lambda t: self._watering_callback(valve_pin_list))
        else:
            self._turn_off_valve()
            self._turn_on_valve_and_wait(valve_pin_list)
    #########################################################
    # _turn_on_valves calls _turn_on_valve_and_wait to start
    # the watering from the first valve as well as a timer
    # with a callback when the watering is done.  When the
    # callback gets triggered, it calls _turn_on_valve_and_wait
    # to start up the next valve in the list, or to stop
    # if the list of valves is empty.
    #########################################################

    def _turn_on_valve_and_wait(self, valve_pin_list):
        if len(valve_pin_list) != 0:
            valve_pin = valve_pin_list[0]
            self.watering_pin = Pin(valve_pin, Pin.OUT)
            self.watering_pin.on()
            print('turned on valve {}'.format(valve_pin_list[0]))
            valve_pin_list = valve_pin_list[1:]
            # Not sure why, but if WATERING_TIME is > 7 minutes, the callback doesn't happen.
            self.tim.init(period=self.watering_ms, mode=Timer.ONE_SHOT,
                          callback=lambda t: self._watering_callback(valve_pin_list))
    #########################################################
    # Listen calls _turn_on_valves when it gets an HTML request
    # that is tagged with 'water_on'.
    # This function gets the watering "work flow" started by
    # sending the list of valve pins to the next method.
    #########################################################

    def _turn_on_valves(self, valve_pins):
        valve_pin_list = list(valve_pins)
        # Kludge to get over wemos won't let me set the callback timer above 7 minutes.
        self.num_five_min_called_back = 0
        self._turn_on_valve_and_wait(valve_pin_list)
    #########################################################
    # Listen is the main method called after initialization.  This
    # function creates a web server and then listens for the
    # stop and start (watering) html commands.  I've been
    # using Angry IP to figure out what IP address to connect
    # to.
    #
    # I also have/had plans to change the watering time.  But
    # at the moment that is not implemented.  Right now the
    # WATERING_TIME constant is set to 15 (for 15 minutes).
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
            exit_listen = request.find('exit')
            watering_time = request.find('water_time')
            hello_listen = request.find('hello')
            if (hello_listen != -1 and hello_listen < 10):
                # Command sent to start watering.
                self._send_response(conn, 'hello')

            if (start_watering != -1 and start_watering < 10):
                # Command sent to start watering.
                self._send_response(conn, 'start watering')
                self._turn_on_valves(self.pins_set_to_valves)

            elif (stop_watering != -1 and stop_watering < 10):

                # Command sent to stop watering.
                self._send_response(conn, 'stop watering')
                # THere's only one valve on at a time.
                self._turn_off_valve()
            elif (watering_time != -1 and watering_time < 10):
                # TODO: Change watering time.
                self._send_response(conn, 'changing watering time')
            elif (exit_listen != -1 and exit_listen < 10):
                self._turn_off_valve()
                conn.close()
                print('received a request to exit, buh-bye')
                break
            else:
                print('received packet.  Was not a water request')
            conn.close()
        s.close()
