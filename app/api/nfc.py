from flask import Blueprint, request, abort, jsonify, g
from .. import db
from ..util import get_db_object_list, InvalidUsage, info
from .auth import require_auth, require_admin
from .action import start_action_from_id

api = Blueprint('NFC API', __name__)

@api.route('/tag/add', methods=['POST'])
@require_admin
def tag_add():
    theid = request.json.get("id")
    if theid is None:
        raise InvalidUsage("id attribute is required")

    action_id = request.json.get("action_id")
    if action_id is None:
        raise InvalidUsage("action_id attribute is required")

    # Make sure that the tag does not exist.
    tag = db.Tag.get(g.db, id=theid)
    if tag:
        raise InvalidUsage("tag with the given id exists already")

    tag = db.Tag.new(g.db, theid, action_id)
    info('New NFC tag with ID', theid, "created")
    return jsonify({'msg': 'Tag created', 'tag': tag.to_dict()})

@api.route('/tag/edit', methods=['POST'])
@require_admin
def tag_edit():
    tag_id = request.json.get("id")
    if tag_id is None:
        raise InvalidUsage("id attribute is required")

    # Make sure that the tag exists.
    tag = db.Tag.get(g.db, id=tag_id)
    if tag is None:
        raise InvalidUsage("tag with the given id does not exist")

    tag.action_id = request.json.get("action_id")
    if tag.action_id is None:
        raise InvalidUsage("action_id attribute is required")

    tag.save(g.db)
    info("NFC tag with ID", tag_id, "assigned to action", tag.action_id)
    return jsonify({'msg': 'tag saved', 'tag': tag.to_dict()})

@api.route('/tag/list', methods=['POST'])
@require_admin
def tag_list():
    return get_db_object_list(g.db, db.Tag)

@api.route('/tag/remove', methods=['POST'])
@require_admin
def tag_remove():
    id_list = request.json.get("id")
    if id_list is None:
        raise InvalidUsage("id attribute is required")
    db.Tag.remove_many(g.db, id=id_list)
    info("NFC tags removed:", ' '.join(id_list))
    return jsonify({'msg': 'Tag removed', 'id': id_list})

@api.route('/tag/remove_all', methods=['POST'])
@require_admin
def tag_remove_all():
    db.Tag.remove_many(g.db)
    info("All NFC tags removed")
    return jsonify({'msg': 'All tags removed'})

@api.route('/tag/start', methods=['POST'])
@require_admin
def tag_start(self):
    tag_id = request.json.get("id")
    if tag_id is None:
        raise InvalidUsage("id attribute is required")

    tag = db.Tag.get(g.db, id=tag_id)
    if tag:
        raise InvalidUsage("tag with the given id does not exist")
    info("Starting action", tag.action_id, "from NFC tag", tag_id)
    return start_action_from_id(tag.action_id)
