import time
from doormanhub.logs import err, info

try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO
except ImportError:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    err("RPi.GPIO Python module is not installed; using Mock.GPIO")
    import Mock.GPIO as GPIO

RELAIS1_PIN = 17 # TODO
RELAIS2_PIN = 18 # TODO
RELAIS_PINS = [RELAIS1_PIN, RELAIS2_PIN]

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAIS1_PIN, GPIO.OUT)
GPIO.setup(RELAIS2_PIN, GPIO.OUT)
GPIO.output(RELAIS1_PIN, GPIO.LOW)
GPIO.output(RELAIS2_PIN, GPIO.LOW)

"""
Returns a list of tuples representing attached relais devices, using the following logic:

    [
      (device1_id, (device1_status, device2_status, ...)),
      (device2_id, (device1_status, device2_status, ...)),
      ...
    ]

- device_id is a unique string (the USB HID serial number)
- number_of_relais is an integer, except if the type of relais can not be identified,
in which case number_of_relais is None.
- relais_status is boolean, True means on, False means off,

"""
def discover():
    devices = []
    relais1_on = GPIO.input(RELAIS1_PIN)
    relais2_on = GPIO.input(RELAIS2_PIN)

    return [
      ("GPIO-Relais-Hat", (relais1_on, relais2_on)),
    ]

def switch(device_id, switch_id, on):
    switch_id = int(switch_id)
    pin = RELAIS_PINS[switch_id - 1]
    on = GPIO.input(pin)
    status = GPIO.HIGH if on else GPIO.LOW
    GPIO.output(pin, status)
    info("Switched relais %s to %s", switch_id, 'on' if status == GPIO.HIGH else 'off')

def switch_temporary(device_id, switch_id, seconds, on=True):
    try:
        switch(device_id, switch_id, on)
        time.sleep(seconds)
    except Exception as e:
        raise
    finally:
        switch(device_id, switch_id, not on)

if __name__ == '__main__':
    print(discover())
    switch_temporary(None, 2, 2)
