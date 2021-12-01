import os
import re
import string
import random
import subprocess
import hashlib
import smtplib
from contextlib import closing
from email.mime.text import MIMEText
from flask import request, g, jsonify, current_app
from . import db
from . import const

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['msg'] = self.message
        return rv

def safe_str(*obj_list):
    result = []
    for obj in obj_list:
        if isinstance(obj, str):
            result.append(obj)
        else:
            result.append(str(obj))
    return ' '.join(result)

def log(user, severity, *msg):
    if isinstance(user, str):
        uname = user
    elif user is not None:
        uname = user.email
    else:
        try:
            uname = g.user.email # raises RuntimeError outside request context
        except (RuntimeError, AttributeError):
            uname = 'system'

    try:
        client_ip = request.remote_addr # raises RuntimeError outside request context
    except RuntimeError:
        client_ip = None

    try:
        thedb = g.db # raises RuntimeError outside request context
    except RuntimeError:
        thedb = None
    if thedb is not None:
        db.Event.new(thedb, uname, client_ip, severity, safe_str(*msg))
    else:
        with closing(db.connect(const.db_file)) as thedb:
            db.Event.new(thedb, uname, client_ip, severity, safe_str(*msg))

def debug(*msg):
    log(None, 'debug', *msg)

def info(*msg):
    log(None, 'info', *msg)

def err(*msg):
    log(None, 'error', *msg)

def rand_string(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_db_object_list(conn, cls):
    try:
        limit = int(request.json.get("limit", 25))
    except TypeError:
        raise InvalidUsage('limit must be an integer: ' + str(limit))
    try:
        offset = int(request.json.get("offset", 0))
    except TypeError:
        raise InvalidUsage('offset must be an integer: ' + str(offset))
    thelist = cls.list(g.db, limit, offset)
    count = cls.count(g.db)
    return jsonify({"msg": "success",
	            "list": [item.get_info(conn) for item in thelist],
	            "total": count})

def password_hash(password):
    if password is not None:
        return hashlib.sha256(password + const.crypto_salt).hexdigest()
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
