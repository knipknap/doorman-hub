from flask import Blueprint, request, abort, jsonify, g, current_app
from .. import const
from ..util import send_mail, InvalidUsage, info, debug, collect_debug_info, err, reboot
from .auth import require_auth, require_admin

api = Blueprint('Core Utility API', __name__)

@api.route('/message/send', methods=['POST'])
@require_admin
def message_send():
    subject = request.json.get("subject")
    if subject is None:
        raise InvalidUsage("subject attribute is required")

    body = request.json.get("body")
    if body is None:
        raise InvalidUsage("body attribute is required")

    body += "\n\n" + collect_debug_info()
    try:
        send_mail(const.support_email, subject, body)
    except Exception as e:
        err('Support message could not be sent due do an error:', e)
        abort(500, str(e))
    info('Support message was sent')
    return jsonify({'msg': 'Your support request has been sent. We will get back to you soon!'})

@api.route('/debug/info', methods=['POST'])
@require_admin
def debug_info():
    result = collect_debug_info()
    debug('Debug info was collected')
    return jsonify({'msg': 'Debug info collected', 'info': result})

@api.route('/system/reboot', methods=['POST'])
@require_admin
def system_reboot():
    info('Rebooting system as per user request')
    try:
        reboot()
    except Exception as e:
        err("Triggering system reboot failed:", e)
        return jsonify({'msg': 'Failed to trigger system reboot'})
    info('System reboot triggered')
    return jsonify({'msg': 'System rebooting'})
