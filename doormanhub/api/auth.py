from flask import Blueprint, request, abort, jsonify, g
from functools import wraps
from datetime import datetime
from .. import const
from ..db import Session, User
from ..util import hash_password
from ..dbutil import get_db_object_list, model_to_dict
from ..exceptions import InvalidUsage
from ..logs import log, info, debug, err

# Import external libraries.
import apiclient
from googleapiclient import errors
from googleapiclient.discovery import build
oauth = build('oauth2', 'v2', developerKey = const.google_api_key)

def _getsid():
    sid = request.cookies.get("sid")
    if sid is None and hasattr(request, "json"):
        try:
            sid = request.json.get("sid")
        except AttributeError:
            sid = None
    return sid

def attempt_auth():
    sid = _getsid()
    if sid is None:
        return

    session = Session.get_or_none(Session.id == sid)
    if session is None or not session.is_valid():
        return

    user = User.get_or_none(User.id == session.user_id)
    if user is None:
        return

    if not user.is_authorized():
        return
    g.user = user

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user is None or not g.user.is_authorized():
            abort(401)
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        if not g.user.is_admin:
            abort(401)
        return func(*args, **kwargs)
    return wrapper

api = Blueprint('Authentication API', __name__)

@api.route('/session/start', methods=['POST'])
def session_start():
    email = request.json.get("username", request.json.get("email"))
    if email is None:
        raise InvalidUsage("email attribute is required")

    password = request.json.get("password")
    if password is None:
        raise InvalidUsage("password attribute is required")

    user = User.get_or_none(User.email == email)
    if user is None or not user.check_password(password):
        err("login failed:", email)
        abort(401)

    expires = datetime.now() + const.session_timeout
    session = Session.create(user=user, expires=expires)
    if session is None:
        err("Failed to create session:", email)
        abort(500, "session creation failed")

    log(user, 'info', "User logged in (via password)")
    return jsonify({"msg": "login successful",
                    "email": user.email,
                    "sid": session.id,
                    "sid_expires": session.expires})

@api.route('/session/start_google', methods=['POST'])
def session_start_google():
    # Check whether a Google id_token was passed via HTTP.
    id_token = request.json.get("id_token")
    if id_token is None:
        raise InvalidUsage("id_token is required for google authentication")

    # Ask Google whether this token is valid.
    google_request = oauth.tokeninfo(id_token=id_token, fields='email')
    try:
        result = google_request.execute()
    except errors.HttpError as e:
        abort(500, "google authentication error: " + str(e))

    # Check that the user id (=Google email address) is contained within the token.
    try:
        email = result['email']
    except KeyError as e:
        abort(500, "google token contains no email address")

    user = User.get_or_none(User.email == email)
    if user is None:
        err("Google authentication for user", email, "failed")
        abort(401)

    expires = datetime.now() + const.session_timeout
    session = Session.create(user=user, expires=expires)
    if session is None:
        abort(500, "session creation failed")

    log(user, 'info', "user logged in (via Google)")
    return jsonify({"msg": "login successful",
                    "email": user.email,
                    "sid": session.id,
                    "sid_expires": session.expires})

@api.route('/session/check', methods=['POST'])
def session_check():
    sid = _getsid()
    session = Session.get_or_none(Session.id == sid)
    if session is None or not session.is_valid():
        abort(401)
    return jsonify({"msg": "session is valid", "sid": session.id})

@api.route('/session/end', methods=['POST'])
def session_end():
    sid = _getsid()
    session = Session.get_or_none(Session.id == sid)
    if session is not None:
        session.delete_instance()
        debug("user with id", session.user_id, "logged out")
    else:
        debug("session id", sid, "logged out")
    return jsonify({"msg": "logout successful"})

@api.route('/user/define_admin', methods=['POST'])
def define_admin():
    # If we do not have an admin account defined yet, add one now.
    admin = User.get_or_none(User.is_active == True, User.is_admin == True)
    if admin is not None:
        raise InvalidUsage("admin account already exists")

    email = request.json.get("username", request.json.get("email"))
    if email is None:
        raise InvalidUsage("email attribute is required")

    password = request.json.get("password")
    if password is None:
        raise InvalidUsage("password attribute is required")

    user = User.create(email=email,
                       full_name='Admin',
                       password=hash_password(password),
                       is_admin=True)
    log(user, 'info', 'initial admin account defined')
    return jsonify({'msg': 'Admin rights granted', 'email': user.email})

@api.route('/user/add', methods=['POST'])
@require_admin
def user_add():
    email = request.json.get("username", request.json.get("email"))
    if email is None:
        raise InvalidUsage("email attribute is required")

    full_name = request.json.get("full_name")
    if full_name is None:
        raise InvalidUsage("full_name attribute is required")

    password = request.json.get("password")
    if password is None:
        raise InvalidUsage("password attribute is required")

    is_admin = request.json.get("is_admin")
    if is_admin is None:
        raise InvalidUsage("is_admin attribute is required")

    is_active = request.json.get("is_active")
    if is_active is None:
        raise InvalidUsage("is_active attribute is required")

    # Make sure that the user does not exist.
    user = User.get_or_none(email=email)
    if user:
        raise InvalidUsage("user with the given email address exists already")

    user = User.create(email=email,
                       full_name=full_name,
                       password=password,
                       is_admin=is_admin,
                       is_active=is_active)
    info('user created:', user.email)
    user_dict = model_to_dict(user)
    return jsonify({'msg': 'User created', 'user': user_dict})

@api.route('/user/edit', methods=['POST'])
@require_admin
def user_edit():
    user_id = request.json.get("id")
    if user_id is None:
        raise InvalidUsage("id attribute is required")

    # Make sure that the user exists.
    user = User.get_or_none(User.id == user_id)
    if user is None:
        raise InvalidUsage("user with id " + str(user_id) + " not found")

    user.email = request.json.get("username", request.json.get("email"))
    if user.email is None:
        raise InvalidUsage("email attribute is required")

    user.full_name = request.json.get("full_name")
    if user.full_name is None:
        raise InvalidUsage("full_name attribute is required")

    user.is_admin = request.json.get("is_admin") and True or False
    user.is_active = request.json.get("is_active") and True or False
    password = request.json.get("password")
    if password:
        user.set_password(password)

    user.save()
    info('user changed:', user.email)
    user_dict = model_to_dict(user)
    return jsonify({'msg': 'User saved', 'user': user_dict})

@api.route('/user/list', methods=['POST'])
@require_admin
def user_list():
    return get_db_object_list(User)

@api.route('/user/remove', methods=['POST'])
@require_admin
def user_remove():
    email = request.json.get("username", request.json.get("email"))
    if email is None:
        raise InvalidUsage("email attribute is required")
    User.delete().where(User.email == email).execute()
    info('users deleted:', ', '.join(list(email)))
    return jsonify({'msg': 'User removed', 'email': email})

@api.route('/user/remove_all', methods=['POST'])
@require_admin
def user_remove_all():
    User.delete().execute()
    info('all users deleted')
    return jsonify({'msg': 'All users removed'})
