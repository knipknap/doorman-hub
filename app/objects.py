class Sensor(object):
    def __init__(self, theid, name):
        self.id = str(theid)
        self.name = name

    def to_dict(self):
        return {'id': self.id,
                'name': self.name}

class Actor(object):
    def __init__(self, theid, name):
        self.id = str(theid)
        self.name = name

    def to_dict(self):
        return {'id': self.id,
                'name': self.name}

    def trigger(self, device, params):
        raise NotImplementedError()

class Device(object):
    def __init__(self, theid, name, interface):
        self.id = str(theid)
        self.name = name
        self.interface = interface
        self.sensors = []
        self.actors = {}

    def to_dict(self):
        actors = [v.to_dict() for v in self.actors.itervalues()]
        return {'id': self.id,
                'name': self.name,
                'interface': self.interface,
                'sensors': [s.to_dict() for s in self.sensors],
                'actors': actors}

    def add_actor(self, actor):
        self.actors[str(actor.id)] = actor

    def get_actor_from_id(self, actor_id):
        return self.actors.get(actor_id)
