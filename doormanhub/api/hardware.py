from flask import Blueprint, request, jsonify, current_app
from ..exceptions import InvalidUsage
from .auth import require_auth

api = Blueprint('Hardware API', __name__)

@api.route('/device/list', methods=['POST'])
@require_auth
def device_list():
    return jsonify({'msg': 'success',
                    'total': len(current_app.devices),
                    'list': [d.to_dict() for d in current_app.devices.values()]})

@api.route('/actor/list', methods=['POST'])
@require_auth
def actor_list():
    device_id = request.json.get("device_id")
    if device_id is None:
        raise InvalidUsage("device_id attribute is required")

    device = current_app.devices.get(device_id)
    if device is None:
        raise InvalidUsage("unknown device id " + str(device_id))
    return jsonify({'msg': 'success',
                    'actors': [a.to_dict() for a in device.actors.values()]})
