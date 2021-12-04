from flask import request, g
from .db import Event

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

    Event.create(user_id=uname,
                 client_ip=client_ip,
                 severity=severity,
                 event_text=safe_str(*msg))

def debug(*msg):
    log(None, 'debug', *msg)

def info(*msg):
    log(None, 'info', *msg)

def err(*msg):
    log(None, 'error', *msg)
