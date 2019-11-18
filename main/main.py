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

event_sinks = set()
d = dht.DHT11(machine.Pin(17))

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
    


def temperature(req, resp):
    
    jsonData = {"temperature":27,"humidity": 90}
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


loop = uasyncio.get_event_loop()
#loop.create_task(push_count())
#loop.create_task(set_led())

app = picoweb.WebApp(__name__, ROUTES)
app.run(host='0.0.0.0', debug=-1)
#app.run(host='0.0.0.0')




