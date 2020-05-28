import network
import socket
import ure
import time
ap_ssid = "WaterPuck"
ap_password = "happyday"
ap_authmode = 3
wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)
server_socket = None


def get_connection():
    if wlan_sta.isconnected():
        return wlan_sta
    else:
        print('wlan is not connected.')
        start()
        return wlan_sta


def do_connect(ssid, password):
    # Wait for wifi to be available.
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        print('\nNetwork config: ', wlan_sta.ifconfig())
        return True
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    while not wlan_sta.isConnected:
        time.sleep(0.1)
        print('.', end='')
    print('\nConnected. Network config: ', wlan_sta.ifconfig())


def send_header(client, status_code=200, content_length=None):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8')for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall("""        <html>
            <h1 style="color: #5e9ca0; text-align: center;">
                <span style="color: #ff0000;">
                    Wi-Fi Client Setup
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall("""                        <tr>
                            <td colspan="2">
                                <input type="radio" name="ssid" value="{0}" />{0}
                            </td>
                        </tr>
        """  .format(ssid))
    client.sendall("""                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                    </tbody>
                </table>
                <p style="text-align: center;">
                    <input type="submit" value="Submit" />
                </p>
            </form>
            <p>&nbsp;</p>
            <hr />
        </html>
    """)
    client.close()


def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)
    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    try:
        ssid = match.group(1).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")
    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False
    if do_connect(ssid, password):
        response = """        <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
    else:
        response = """        <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket
    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    stop()
    wlan_sta.active(True)
    wlan_ap.active(True)
    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)
    server_socket = socket.socket()
    server_socket.bind(addr)
    print('listening....')
    server_socket.listen(1)
    print('Connect to WiFi ssid '+ap_ssid+', default password: '+ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)
    while True:
        if wlan_sta.isconnected():
            print('in start wlan is connected.')
            return True
        client, addr = server_socket.accept()
        print('client connected from', addr)
        try:
            client.settimeout(5.0)
            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass
            print("Request is: {}".format(request))
            if "HTTP" not in request:
                continue
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP",
                                 request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search(
                    "(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))
            if url == "":
                handle_root(client)
            elif url == "configure":
                handle_configure(client, request)
            else:
                handle_not_found(client, url)
        finally:
            client.close()
# Created by pyminifier (https://github.com/liftoff/pyminifier)
