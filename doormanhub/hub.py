import sys
import os
import imp
from .db import db, User
from . import const
from flask import Flask, render_template, jsonify, g, redirect, send_from_directory
from .api import action, auth, hardware, log, nfc, utility
from .api.auth import attempt_auth, require_admin
from .exceptions import InvalidUsage
from .util import getserial
from .logs import debug
from .version import __version__

app = Flask(__name__, static_url_path='')
app.config['VERSION'] = __version__
app.config['MEDIA_DIR'] = 'static'
app.debug = True

app.register_blueprint(action.api, url_prefix='/api/action/1.0')
app.register_blueprint(auth.api, url_prefix='/api/auth/1.0')
app.register_blueprint(hardware.api, url_prefix='/api/hardware/1.0')
app.register_blueprint(log.api, url_prefix='/api/log/1.0')
app.register_blueprint(nfc.api, url_prefix='/api/nfc/1.0')
app.register_blueprint(utility.api, url_prefix='/api/utility/1.0')

def load_drivers(driver_dir):
    sys.path.append(driver_dir)
    driver_dirs = [o for o in os.listdir(driver_dir)
                   if os.path.isdir(os.path.join(driver_dir, o))]

    for name in driver_dirs:
        print("Loading", name)
        fp, pathname, description = imp.find_module(name)
        module = imp.load_module(name, fp, pathname, description)
        app.drivers.append(module)
        driver = getattr(module, 'driver')
        if driver is None:
            print(name + ': Driver without a valid "driver" module. Skipping.')
            continue
        on_init = getattr(driver, 'on_init')
        if on_init is not None:
            print("Calling", name + ".driver.on_init()")
            debug('Calling', name+'.driver.on_init()')
            on_init(app)
        debug('Driver loaded successfully:', name)

app.drivers = []
app.devices = {}
load_drivers(os.path.join(os.path.dirname(__file__), 'drivers'))
driver_names = ', '.join([d.__name__ for d in app.drivers])
device_names = ', '.join(app.devices.keys())

debug('Drivers:', driver_names)
debug('Devices:', device_names)

@app.errorhandler(InvalidUsage)
def custom400(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.before_request
def before_request():
    g.user = None
    attempt_auth()

@app.teardown_request
def teardown_request(exception):
    db.close()

@app.route('/')
def login():
    admin = User.get_or_none(User.is_active == True, User.is_admin == True)
    if admin is None:
        return render_template('init.html')
    if g.user:
        return redirect('home')
    return render_template('login.html')

@app.route('/home')
def events():
    if g.user.is_admin:
        return render_template('events.html')
    return render_template('mobile_home.html')

@app.route('/users')
@require_admin
def users():
    return render_template('users.html')

@app.route('/actions')
@require_admin
def actions():
    return render_template('actions.html')

@app.route('/tags')
@require_admin
def tags():
    return render_template('tags.html')

@app.route('/devices')
@require_admin
def devices():
    return render_template('devices.html')

@app.route('/about')
@require_admin
def about():
    return render_template('about.html', serial=getserial())

@app.route('/support')
@require_admin
def support():
    return render_template('support.html')

@app.route('/{}/<path>'.format(app.config['MEDIA_DIR']))
def send_js(path):
    return send_from_directory(const.static_dir, path)

if __name__ == '__main__':
    app.run()
