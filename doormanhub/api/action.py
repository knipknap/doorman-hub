from flask import Blueprint, request, jsonify, g, current_app
from ..db import Action
from ..dbutil import get_db_object_list, model_to_dict
from ..exceptions import InvalidUsage
from ..logs import info, debug, err
from .auth import require_auth, require_admin

api = Blueprint('Action API', __name__)

@api.route('/action/add', methods=['POST'])
@require_admin
def action_add():
    name = request.json.get("name")
    if name is None:
        raise InvalidUsage("name attribute is required")

    description = request.json.get("description")
    if description is None:
        raise InvalidUsage("description attribute is required")

    device_id = request.json.get("device_id")
    if device_id is None:
        raise InvalidUsage("device_id attribute is required")
    device = current_app.devices.get(device_id)
    if device is None:
        raise InvalidUsage("unknown device_id " + str(device_id))

    actor_id = request.json.get("actor_id")
    if actor_id is None:
        raise InvalidUsage("actor_id attribute is required")
    actor = device.get_actor_from_id(actor_id)
    if actor is None:
        raise InvalidUsage("unknown actor_id " + str(actor_id))

    params = request.json.get("params")
    if params is None:
        raise InvalidUsage("params attribute is required")

    action = Action.create(name=name,
                           description=description,
                           device_id=device_id,
                           actor_id=actor_id,
                           params=params)

    info("action created:", action.name, "(id is " + str(action.id) + ")")
    action_dict = model_to_dict(action)
    return jsonify({'msg': 'Action created', 'action': action_dict})

@api.route('/action/edit', methods=['POST'])
@require_admin
def action_edit():
    action_id = request.json.get("id")
    if action_id is None:
        raise InvalidUsage("id attribute is required")

    # Make sure that the tag exists.
    action = Action.select().get_or_none(Action.id == action_id)
    if action is None:
        raise InvalidUsage("action with the given id does not exist")

    action.name = request.json.get("name")
    if action.name is None:
        raise InvalidUsage("name attribute is required")

    action.description = request.json.get("description")
    if action.description is None:
        raise InvalidUsage("description attribute is required")

    action.device_id = request.json.get("device_id")
    if action.device_id is None:
        raise InvalidUsage("device_id attribute is required")
    device = current_app.devices.get(action.device_id)
    if device is None:
        raise InvalidUsage("unknown device_id " + str(action.device_id))

    action.actor_id = request.json.get("actor_id")
    if action.actor_id is None:
        raise InvalidUsage("actor_id attribute is required")
    actor = device.get_actor_from_id(action.actor_id)
    if actor is None:
        raise InvalidUsage("unknown actor_id " + str(action.actor_id))

    action.params = request.json.get("params")
    if action.params is None:
        raise InvalidUsage("params attribute is required")

    action.save()
    info("action changed:", action.name, "(id is " + str(action.id) + ")")
    action_dict = model_to_dict(action)
    return jsonify({'msg': 'Action saved', 'action': action_dict})

@api.route('/action/list', methods=['POST'])
@require_auth
def action_list():
    return get_db_object_list(Action)

@api.route('/action/remove', methods=['POST'])
@require_admin
def action_remove():
    id_list = request.json.get("id")
    if id_list is None:
        raise InvalidUsage("id attribute is required")
    Action.delete().where(Action.id.in_(id_list)).execute()
    info("actions removed:", '(' + ' '.join(id_list) + ')')
    return jsonify({'msg': 'Action removed', 'id': id_list})

@api.route('/action/remove_all', methods=['POST'])
@require_admin
def action_remove_all():
    Action.delete().execute()
    info("all actions removed")
    return jsonify({'msg': 'All actions removed'})

"""
Separate function to allow for other APIs to import it.
"""
def start_action_from_id(action_id):
    action = Action.get_or_none(Action.id == action_id)
    if action is None:
        raise InvalidUsage("action with the given id does not exist")

    device = current_app.devices.get(action.device_id)
    if device is None:
        raise InvalidUsage("action references an unknown device" + str(action.device_id))
    actor = device.get_actor_from_id(action.actor_id)
    if actor is None:
        raise InvalidUsage("action references an unknown actor:" + str(action.actor_id))

    debug("attempting to start action:", action.name)
    try:
        actor.trigger(device, action.params)
    except Exception as e:
        err('action "' + action.name + '"',
            "(id " + str(action.id) + ')',
            "failed:", e)
        raise
    info("action started:", action.name)
    action_dict = model_to_dict(action)
    return jsonify({'msg': 'Action started', 'action': action_dict})

@api.route('/action/start', methods=['POST'])
@require_auth
def action_start():
    action_id = request.json.get("id")
    if action_id is None:
        raise InvalidUsage("id attribute is required")
    return start_action_from_id(action_id)
