import peewee
from flask import request, g, jsonify, current_app
from playhouse.shortcuts import model_to_dict as _model2dict
from .exceptions import InvalidUsage

def model_to_dict(obj):
    thedict = {}
    for key, value in _model2dict(obj).items():
        field = obj._meta.fields[key]
        if isinstance(field, peewee.DateTimeField):
            thedict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            thedict[key] = value
    return thedict

def get_db_object_list(cls):
    try:
        limit = int(request.json.get("limit", 25))
    except TypeError:
        raise InvalidUsage('limit must be an integer: ' + str(limit))
    try:
        offset = int(request.json.get("offset", 0))
    except TypeError:
        raise InvalidUsage('offset must be an integer: ' + str(offset))

    thelist = cls.select().offset(offset).limit(limit)
    thelist = [model_to_dict(m) for m in thelist]
    count = cls.select().count()
    return jsonify({"msg": "success", "list": thelist, "total": count})
