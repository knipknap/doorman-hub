from flask import Blueprint, request, abort, jsonify, g
from .. import db
from ..util import get_db_object_list, InvalidUsage, info
from .auth import require_auth, require_admin

api = Blueprint('Log API', __name__)

@api.route('/event/list', methods=['POST'])
@require_admin
def event_list():
    return get_db_object_list(g.db, db.Event)

@api.route('/event/remove_all', methods=['POST'])
@require_admin
def event_remove_all():
    db.Event.remove_many(g.db)
    info('all logs cleared')
    return jsonify({'msg': 'All events removed'})
