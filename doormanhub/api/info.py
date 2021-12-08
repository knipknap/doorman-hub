from flask import Blueprint, jsonify

api = Blueprint('Info API', __name__)

@api.route('/hello', methods=['GET'])
def session_start():
    return jsonify({"msg": "hello"})
