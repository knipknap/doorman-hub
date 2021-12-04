import json
from peewee import *
from datetime import datetime
from . import const
from .util import rand_string, hash_password

# Connect to the database. Gracefully fall back to Sqlite to
# make things easier to test.
if const.db_host:
    db = PostgresqlDatabase(const.db_db,
                            host=const.db_host,
                            port=const.db_port,
                            user=const.db_user,
                            passwd=const.db_password)
else:
    db = SqliteDatabase(const.db_file)

class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)

class OrderedModel(Model):
    class Meta:
        order_by = []

    # Simple re-implementation of default ordering that was removed in peewee 3.x
    # Ideally, ordering should always be explicitly set in query, but this can be
    # very handy, esp. for auto-scaffolding frameworks like flask-admin
    @classmethod
    def select(cls, *fields):
        order_by = []

        for field_name in cls._meta.order_by:
            if field_name.startswith('-'):
                order_by.append(getattr(cls, field_name[1:]).desc())
            else:
                order_by.append(getattr(cls, field_name))

        return super(OrderedModel, cls).select(*fields).order_by(*order_by)

class User(OrderedModel):
    email = CharField(max_length=100, unique=True, index=True)
    full_name = CharField(max_length=100, default='')
    password = CharField(max_length=65, null=True)
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=True)

    class Meta:
        database = db
        order_by = ['email']

    def __str__(self):
        return str(self.id) + '(' + self.email + ')'

    def is_authorized(self):
        return self.id is not None and self.is_active

    def set_password(self, password):
        self.password = hash_password(password)

    def check_password(self, password):
        return self.password == hash_password(password)

class Session(Model):
    id = CharField(max_length=21, primary_key=True, default=rand_string, index=True)
    user = ForeignKeyField(User, backref='sessions')
    expires = DateTimeField()
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = db

    def is_valid(self):
        return self.expires >= datetime.now()

class Action(OrderedModel):
    name = CharField(max_length=40, unique=True, index=True)
    description = CharField(max_length=200, default='')
    device_id = CharField(max_length=100)
    actor_id = CharField(max_length=100)
    params = JSONField()

    class Meta:
        database = db
        order_by = ['name']

    def __str__(self):
        return str(self.id) + '(' + self.name + ')'

class Tag(Model):
    id = CharField(max_length=129, primary_key=True, index=True)
    action = ForeignKeyField(Action, backref='tags')

    class Meta:
        database = db

    def __str__(self):
        return self.id

class Event(OrderedModel):
    user_id = CharField(max_length=100)
    client_ip = CharField(max_length=46, null=True)
    severity = CharField(max_length=10)
    event_text = CharField(max_length=255)
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        order_by = ['-timestamp']

    def __str__(self):
        return str(self.timestamp) \
             + ', ' + self.severity + '/' + self.user_id \
             + ': ' + self.event_text

# Create DB tables if they do not yet exist.
with db:
    db.create_tables([User, Session, Action, Event, Tag])
