import time
from doormanhub.logs import err, info

try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO
except ImportError:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    err("RPi.GPIO Python module is not installed; using Mock.GPIO")
    import Mock.GPIO as GPIO

device_name = "GPIO-Relais-Hat"

RELAIS1_GPIO = 15
RELAIS2_GPIO = 29
RELAIS_GPIOS = [RELAIS1_GPIO, RELAIS2_GPIO]

GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAIS1_GPIO, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(RELAIS2_GPIO, GPIO.OUT, initial=GPIO.LOW)

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
    relais1_on = GPIO.input(RELAIS1_GPIO)
    relais2_on = GPIO.input(RELAIS2_GPIO)

    return [
      (device_name, (relais1_on, relais2_on)),
    ]

def switch(device_id, switch_id, on):
    switch_id = int(switch_id)
    gpio = RELAIS_GPIOS[switch_id - 1]
    status = GPIO.HIGH if on else GPIO.LOW
    GPIO.output(gpio, status)
    status_str = 'on' if status == GPIO.HIGH else 'off'
    info("{}: Switched relais {} to {}".format(device_name, switch_id, status_str))

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
