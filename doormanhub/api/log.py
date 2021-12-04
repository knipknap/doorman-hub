from flask import Blueprint, jsonify
from ..db import Event
from ..dbutil import get_db_object_list
from ..logs import info
from .auth import require_admin

api = Blueprint('Log API', __name__)

@api.route('/event/list', methods=['POST'])
@require_admin
def event_list():
    return get_db_object_list(Event)

@api.route('/event/remove_all', methods=['POST'])
@require_admin
def event_remove_all():
    Event.delete().execute()
    info('all logs cleared')
    return jsonify({'msg': 'All events removed'})
