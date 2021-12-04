import os
import re
import string
import random
import subprocess
import hashlib
import smtplib
from email.mime.text import MIMEText
from . import const

def rand_string(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def hash_password(password):
    if password is not None:
        password = password.encode('utf-8')
        salt = const.crypto_salt.encode('utf-8')
        return hashlib.sha256(password + salt).hexdigest()
    return None

def getserial():
    serial_re = re.compile(r'Serial\s*:\s*(\S+)')
    try:
        with open('/proc/cpuinfo','r') as f:
            for line in f:
                match = serial_re.match(line)
                if match is not None:
                    return match.group(1)
    except IOError:
        return "ERROR000000000"
    return "0000000000000000"

def send_mail(to, subject, body):
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = const.smtp_from
    message['To'] = to
    server = smtplib.SMTP(const.smtp_server)
    server.ehlo()
    server.starttls()
    server.login(const.smtp_user, const.smtp_password)
    server.sendmail(const.smtp_from, to, message.as_string())
    server.quit()

def _start_suidtool(name):
    # We have to call an external binary, with SUID set to gain root permissions.
    cmd = os.path.join(os.path.dirname(__file__), '..', 'suidtools', name)
    child = subprocess.Popen([cmd],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    output, err = child.communicate()
    if child.returncode != 0:
        return name + ' quit with exit code ' + str(child.returncode) + ': ' + err
    return output + err

def collect_debug_info():
    return _start_suidtool('techsupport')

def reboot():
    return _start_suidtool('reboot')

if __name__ == '__main__':
    print(getserial())
