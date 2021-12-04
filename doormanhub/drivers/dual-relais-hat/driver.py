from threading import Thread
from doormanhub.objects import Device, Actor
from doormanhub.logs import debug
from .hat import discover, switch, switch_temporary

device_names = {1: '1 relais HAT',
                2: '2 relais HAT',
                4: '4 relais HAT',
                None: 'unknown relais HAT'}

class Relais(Actor):
    def __init__(self, number, on):
        super(Relais, self).__init__(number, "Relais " + str(number))
        self.on = on

    def to_dict(self):
        thedict = super(Relais, self).to_dict()
        thedict['on'] = self.on
        return thedict

    def trigger(self, device, params):
        seconds = params.get('seconds', 0)
        on = bool(params.get('on', True))
        if seconds == 0:
            Thread(target=switch, args=(device.id, self.id, on)).start()
        else:
            Thread(target=switch_temporary,
                   args=(device.id, self.id, seconds, on)).start()

def on_init(app):
    debug('discovering USB HID relais')
    devices = discover()
    if not devices:
        print("no devices found")
        debug('no devices found')
    for device_id, states in devices:
        debug('using relais HUB:', device_id, states)
        name = device_names.get(len(states))
        device = Device(device_id, name, 'USB')
        for i, state in enumerate(states, start=1):
            relais = Relais(i, state)
            device.add_actor(relais)
        app.devices[device_id] = device
