from flask import Blueprint, request, abort, jsonify, g
from ..db import Tag
from ..exceptions import InvalidUsage
from ..dbutil import get_db_object_list, model_to_dict
from ..logs import info
from .auth import require_admin
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
    tag = Tag.get_or_none(Tag.id == theid)
    if tag:
        raise InvalidUsage("tag with the given id exists already")

    tag = Tag.create(id=theid, action_id=action_id)
    info('New NFC tag with ID', theid, "created")
    tag_dict = model_to_dict(tag)
    return jsonify({'msg': 'Tag created', 'tag': tag_dict})

@api.route('/tag/edit', methods=['POST'])
@require_admin
def tag_edit():
    tag_id = request.json.get("id")
    if tag_id is None:
        raise InvalidUsage("id attribute is required")

    # Make sure that the tag exists.
    tag = Tag.get_or_none(Tag.id == tag_id)
    if tag is None:
        raise InvalidUsage("tag with the given id does not exist")

    tag.action_id = request.json.get("action_id")
    if tag.action_id is None:
        raise InvalidUsage("action_id attribute is required")

    tag.save(g.db)
    info("NFC tag with ID", tag_id, "assigned to action", tag.action_id)
    tag_dict = model_to_dict(tag)
    return jsonify({'msg': 'Tag saved', 'tag': tag_dict})

@api.route('/tag/list', methods=['POST'])
@require_admin
def tag_list():
    return get_db_object_list(Tag)

@api.route('/tag/remove', methods=['POST'])
@require_admin
def tag_remove():
    id_list = request.json.get("id")
    if id_list is None:
        raise InvalidUsage("id attribute is required")
    Tag.delete().where(Tag.id.in_(id_list)).execute()
    info("NFC tags removed:", ' '.join(id_list))
    return jsonify({'msg': 'Tag removed', 'id': id_list})

@api.route('/tag/remove_all', methods=['POST'])
@require_admin
def tag_remove_all():
    Tag.delete().execute()
    info("All NFC tags removed")
    return jsonify({'msg': 'All tags removed'})

@api.route('/tag/start', methods=['POST'])
@require_admin
def tag_start(self):
    tag_id = request.json.get("id")
    if tag_id is None:
        raise InvalidUsage("id attribute is required")

    tag = Tag.get_or_none(Tag.id == tag_id)
    if tag:
        raise InvalidUsage("tag with the given id does not exist")
    info("Starting action", tag.action_id, "from NFC tag", tag_id)
    return start_action_from_id(tag.action_id)
