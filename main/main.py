#
# This is a picoweb example showing a Server Side Events (SSE) aka
# EventSource handling. All connecting clients get the same events.
# This is achieved by running a "background service" (a coroutine)
# and "pushing" the same event to each connected client.
#
import uasyncio
import picoweb
import machine
import dht
import ujson
import neopixel
import onewire, ds18x20, time


n = 183
p = 23
np = neopixel.NeoPixel(machine.Pin(p), n)

ds_pin = machine.Pin(22)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

event_sinks = set()

#d = dht.DHT11(machine.Pin(22))

myrandom = (255,0,0)
is_active = False


def set_color(req, resp):
    global myrandom
    if req.method == "POST":
        yield from req.read_form_data()
    else:  # GET, apparently
        # Note: parse_qs() is not a coroutine, but a normal function.
        # But you can call it using yield from too.
        req.parse_qs()

    # Whether form data comes from GET or POST request, once parsed,
    # it's available as req.form dictionary
    myrandom = (int(req.form["r"]),int(req.form["g"]),int(req.form["b"]))
    for i in range (0,n):
        #myrandom = (random.randint(0,256),random.randint(0,256),random.randint(0,256))
        #myrandom = (255,255,255)
        np[i] = myrandom
    np.write()
    yield from picoweb.start_response(resp)
    yield from resp.awrite("r: %s g: %s b: %s" % (req.form["r"],req.form["g"],req.form["b"]))


def led(req, resp):
    
    global is_active
    if req.method == "POST":
        yield from req.read_form_data()
        #print(req.form)
        # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
        _key = next(iter(req.form.keys()))
        json = ujson.loads(_key)
        #print(json)
        is_active = json['active']
        jsonData = {"is_active": is_active}
    
    else:
        jsonData = {"is_active": is_active}

    if is_active:
        for i in range (0,n):
            #myrandom = (random.randint(0,256),random.randint(0,256),random.randint(0,256))
            #myrandom = (255,255,255)
            np[i] = myrandom
        np.write()
    else:
        for i in range (0,n):
            #myrandom = (random.randint(0,256),random.randint(0,256),random.randint(0,256))
            #myrandom = (255,255,255)
            np[i] = (0,0,0)
        np.write()
    print(jsonData)
    encoded = ujson.dumps(jsonData)
    yield from picoweb.start_response(resp, content_type = "application/json")
    #yield from resp.awrite(_key)
    yield from resp.awrite(encoded)

def led_color(req, resp):
    
    jsonData = {"color": 'red'}
    encoded = ujson.dumps(jsonData)
    yield from picoweb.start_response(resp, content_type = "application/json")
    #yield from resp.awrite(_key)
    yield from resp.awrite(encoded)

#
# Webapp part
#

def reset(req, resp):
    machine.reset()


def update(req, resp):
    from main.ota_updater import OTAUpdater
    o = OTAUpdater('https://github.com/WimRoose/esp32-dev')
    result = o.check_for_update_to_install_during_next_reboot()
    jsonData = {"update":result}
    encoded = ujson.dumps(jsonData)
    yield from picoweb.start_response(resp, content_type = "application/json")
    yield from resp.awrite(encoded)
    


def temperature_dht(req, resp):
    
    d.measure()
    temp = d.temperature()
    humidity = d.humidity()
    jsonData = {"temperature":temp,"humidity": humidity}
    encoded = ujson.dumps(jsonData)
    yield from picoweb.start_response(resp, content_type = "application/json")
    yield from resp.awrite(encoded)

def temperature(req, resp):
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        temp = ds_sensor.read_temp(rom)
    jsonData = {"temperature":str(temp),"humidity": '0'}
    encoded = ujson.dumps(jsonData)
    yield from picoweb.start_response(resp, content_type = "application/json")
    yield from resp.awrite(encoded)

def index(req, resp):
    #global random
    #random = (random.randomint(0,256),random.randomint(0,256),random.randomint(0,256))
    yield from picoweb.start_response(resp)
    yield from resp.awrite("""\
<!DOCTYPE html>
<html>
<head>
<script>
var source = new EventSource("events");
source.onmessage = function(event) {
    document.getElementById("result").innerHTML += event.data + "<br>";
}
source.onerror = function(error) {
    console.log(error);
    document.getElementById("result").innerHTML += "EventSource error:" + error + "<br>";
}
</script>
</head>
<body>
<div id="result"></div>
</body>
</html>
""")


def events(req, resp):
    global event_sinks
    print("Event source %r connected" % resp)
    yield from resp.awrite("HTTP/1.0 200 OK\r\n")
    yield from resp.awrite("Content-Type: text/event-stream\r\n")
    yield from resp.awrite("\r\n")
    event_sinks.add(resp)
    return False


ROUTES = [
    ("/", index),
    ("/events", events),
    ("/temperature", temperature),
    ("/update", update),
    ("/reset", reset),
    ("/setled", set_color),
    ("/led", led),
    ("/led/color", led_color),
    
]

#
# Background service part
#

def push_event(ev):
    global event_sinks
    to_del = set()

    for resp in event_sinks:
        try:
            await resp.awrite("data: %s\n\n" % ev)
        except OSError as e:
            print("Event source %r disconnected (%r)" % (resp, e))
            await resp.aclose()
            # Can't remove item from set while iterating, have to have
            # second pass for that (not very efficient).
            to_del.add(resp)

    for resp in to_del:
        event_sinks.remove(resp)


def push_count():
    i = 0
    while 1:
        await push_event("%s" % i)
        i += 1
        await uasyncio.sleep(1)

for i in range (0,n):
        np[i] = myrandom
np.write()
loop = uasyncio.get_event_loop()
#loop.create_task(push_count())
#loop.create_task(set_led())

app = picoweb.WebApp(__name__, ROUTES)
app.run(host='0.0.0.0', debug=-1)
#app.run(host='0.0.0.0')




