import sqlite3
import json
import time
from datetime import datetime, timedelta
from contextlib import closing
from .util import rand_string, password_hash, safe_str

def _mkquery(sql, params):
    values = []
    if params:
        terms = []
        for k, v in params.items():
            if isinstance(v, list):
                p = ','.join('?' * len(v))
                terms.append(k + ' in (' + p + ')')
                values += v
            else:
                terms.append(k + "=?")
                values.append(v)
        sql += ' WHERE ' + ' AND '.join(terms)
    return sql, values

def _mkupdatequery(table, params):
    sql = 'UPDATE ' + table + ' SET '
    values = []
    if params:
        terms = []
        for k, v in params.items():
            terms.append(k + "=?")
            values.append(v)
        sql += ', '.join(terms)
    return sql, values

def _select(conn, sql, order_by, limit, offset, params):
    sql, values = _mkquery(sql, params)
    if order_by:
        sql += " ORDER BY " + order_by
    if limit is None:
        return conn.execute(sql, values)
    sql += " LIMIT ?,?"
    return conn.execute(sql, values + [offset, limit])

def _selectone(conn, cls, sql, params):
    row = _select(conn, sql, '', 1, 0, params).fetchone()
    if row is not None:
        return cls._from_row(row)
    return None

def _count(conn, table, params):
    row = _select(conn, "SELECT COUNT (*) FROM " + table, '', None, None, params).fetchone()
    return row[0]

def _selectmany(conn, cls, sql, order_by, limit, offset, params):
    return [cls._from_row(row) for row in _select(conn, sql, order_by, limit, offset, params)]

class DBObj(object):
    @classmethod
    def _from_row(cls, row):
        obj = cls.__new__(cls)
        obj.__dict__.update(row)
        return obj

    def to_dict(self):
        raise NotImplementedError()

    def get_info(self, conn):
        return self.to_dict()

    '''
    Returns the first object that matches the given search terms.
    '''
    @classmethod
    def get(cls, conn, **kwargs):
        with closing(conn.cursor()) as cursor:
            sql = 'SELECT * FROM ' + cls.__name__.lower()
            return _selectone(cursor, cls, sql, kwargs)

    '''
    Returns the number of matching items.
    '''
    @classmethod
    def count(cls, conn, **kwargs):
        with closing(conn.cursor()) as cursor:
            return _count(cursor, cls.__name__.lower(), kwargs)

    '''
    Returns a list of objects that match the given search terms.
    '''
    @classmethod
    def list(cls, conn, limit=None, offset=0, **kwargs):
        with closing(conn.cursor()) as cursor:
            sql = 'SELECT * FROM ' + cls.__name__.lower()
            return _selectmany(cursor, cls, sql, 'id', limit, offset, kwargs)

    '''
    Deletes multiple objects from the database.
    '''
    @classmethod
    def remove_many(cls, conn, **kwargs):
        sql = "DELETE FROM " + cls.__name__.lower()
        sql, values = _mkquery(sql, kwargs)
        with conn:
            conn.execute(sql, values)

    '''
    Deletes the object from the database (and sets self.id to None).
    '''
    def remove(self, conn):
        query = "DELETE FROM " + self.__class__.__name__.lower() + " WHERE id=?"
        with conn:
            conn.execute(query, (self.id,))
        self.id = None

    '''
    Saves the object to the database. User must already exist in the db.
    '''
    def save(self, conn):
        sql, values = _mkupdatequery(self.__class__.__name__.lower(), self.to_dict())
        sql += " WHERE id=?"
        with conn:
            conn.execute(sql, values + [self.id,])

class Config(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `config` (
          `id` integer NOT NULL PRIMARY KEY,
          `key` varchar(100) NOT NULL UNIQUE,
          `value` varchar(100) NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS config_key ON config (key);
    '''
    def __init__(self, id, key, value):
        self.id = id
        self.key = key
        self.value = value

    def to_dict(self):
        return {'id': self.id,
                'key': self.key,
                'values': self.values}

    def __str__(self):
        return str(self.id) + '(' + self.key + '=' + str(self.value) + ')'

    '''
    Adds a new config value to the database, returns a new Config object.
    '''
    @classmethod
    def new(cls, conn, key, value):
        query = "INSERT INTO config (key, value) VALUES (?, ?)"
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (key, value))
            conn.commit()
            return User(cursor.lastrowid, key, value)

class User(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `user` (
          `id` integer NOT NULL PRIMARY KEY,
          `email` varchar(100) NOT NULL UNIQUE,
          `full_name` varchar(100) NOT NULL DEFAULT '',
          `password` varchar(65) DEFAULT NULL,
          `is_admin` integer(1) NOT NULL DEFAULT '0',
          `is_active` integer(1) NOT NULL DEFAULT '1'
        );
        CREATE INDEX IF NOT EXISTS user_email ON user (email);
        CREATE INDEX IF NOT EXISTS user_full_name ON user (full_name);
        CREATE INDEX IF NOT EXISTS user_is_admin ON user (is_admin);
        CREATE INDEX IF NOT EXISTS user_is_active ON user (is_active);
    '''
    def __init__(self, id, email, full_name, password, is_admin=False, is_active=True):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin
        self.is_active = is_active
        self.password = password

    def to_dict(self):
        return {'id': self.id,
                'email': self.email,
                'full_name': self.full_name,
                'password': self.password,
                'is_admin': self.is_admin,
                'is_active': self.is_active}

    def __str__(self):
        return str(self.id) + '(' + self.email + ')'

    '''
    Adds a new user to the database, returns a new User object.
    '''
    @classmethod
    def new(cls, conn, email, full_name='', password=None, is_admin=False, is_active=True):
        password = password_hash(password)
        query = "INSERT INTO user (email, full_name, password, is_admin, is_active) VALUES (?, ?, ?, ?, ?)"
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (email, full_name, password, is_admin, is_active))
            conn.commit()
            return User(cursor.lastrowid, email, full_name, password, is_admin, is_active)

    def is_authorized(self):
        return self.id is not None and self.is_active

    def set_password(self, password):
        self.password = password_hash(password)

    def check_password(self, password):
        return self.password == password_hash(password)

class Session(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `session` (
          `id` VARCHAR(21) NOT NULL PRIMARY KEY,
          `user_id` integer NOT NULL,
          `expires` INTEGER NOT NULL,
          `created` INTEGER DEFAULT(strftime('%s', 'now')) NOT NULL,
          FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS session_id ON session (id);
    '''
    def __init__(self, id, user_id, expires, created):
        self.id = id
        self.user_id = user_id
        self.expires = expires
        self.created = created

    '''
    Adds a new session to the database, returns a new User object.
    '''
    @classmethod
    def new(cls, conn, user_id, expires):
        # Now is also a good time to delete old sessions.
        query = "DELETE FROM session WHERE expires < strftime('%s', 'now')"
        with closing(conn.cursor()) as cursor:
            cursor.execute(query)
            sid = rand_string()
            query = "INSERT INTO session (id, user_id, expires, created) VALUES (?, ?, ?, ?)"
            now = int(time.time())
            cursor.execute(query, (sid, user_id, expires, now))
            conn.commit()
            return Session(sid, user_id, expires, now)

    def is_valid(self):
        return self.expires >= int(time.time())

class Action(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `action` (
          `id` integer NOT NULL PRIMARY KEY,
          `name` varchar(40) NOT NULL UNIQUE,
          `description` varchar(200) NOT NULL DEFAULT '',
          `device_id` VARCHAR(100) NOT NULL,
          `actor_id` VARCHAR(100) NOT NULL,
          `params` NVARCHAR(5000) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS action_name ON action (name);
    '''
    def __init__(self, theid, name, description, device_id, actor_id, params):
        self.id = theid
        self.name = name
        self.description = description
        self.device_id = device_id
        self.actor_id = actor_id
        self.params = params

    def to_dict(self):
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'device_id': self.device_id,
                'actor_id': self.actor_id,
                'params': self.params}

    def __str__(self):
        return str(self.id) + '(' + self.name + ')'

    @classmethod
    def new(cls, conn, name, description, device_id, actor_id, params):
        query = "INSERT INTO action (name, description, device_id, actor_id, params) VALUES (?, ?, ?, ?, ?)"
        data = name, description, device_id, actor_id, json.dumps(params)
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, data)
            conn.commit()
            return Action(cursor.lastrowid, name, description, device_id, actor_id, params)

    def save(self, conn):
        data = self.to_dict()
        data['params'] = json.dumps(data['params'])
        sql, values = _mkupdatequery(self.__class__.__name__.lower(), data)
        sql += " WHERE id=?"
        with conn:
            conn.execute(sql, values + [self.id,])

    @classmethod
    def get(cls, conn, **kwargs):
        result = super(Action, cls).get(conn, **kwargs)
        result.params = json.loads(result.params)
        return result

class Tag(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `tag` (
          `id` varchar(129) NOT NULL PRIMARY KEY,
          `action_id` integer NOT NULL,
          FOREIGN KEY(action_id) REFERENCES action(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS tag_action_id ON action (id);
    '''
    # INSERT OR IGNORE INTO tag VALUES ('04CFF76A873380', 1);
    def __init__(self, theid, action_id):
        self.id = theid
        self.action_id = action_id

    def to_dict(self):
        return {'id': self.id, 'action_id': self.action_id}

    def get_info(self, conn):
        thedict = self.to_dict()
        thedict['action_name']= Action.get(conn, id=self.action_id).name
        return thedict

    def __str__(self):
        return self.id

    '''
    Adds a new tag to the database, returns a new Tag object.
    '''
    @classmethod
    def new(cls, conn, theid, action_id):
        query = "INSERT INTO tag (id, action_id) VALUES (?, ?)"
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (theid, action_id))
            conn.commit()
            return Tag(cursor.lastrowid, action_id)

class Event(DBObj):
    init_sql = '''
        CREATE TABLE IF NOT EXISTS `event` (
          `id` integer NOT NULL PRIMARY KEY,
          `user_id` varchar(100) NOT NULL,
          `client_ip` varchar(46),
          `severity` varchar(10) NOT NULL,
          `event_text` varchar(255) NOT NULL,
          `timestamp` DATETIME DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS event_timestamp ON event (timestamp);
    '''
    def __init__(self, id, user_id, client_ip, severity, event_text):
        self.id = id
        self.user_id = user_id
        self.client_ip = client_ip
        self.severity = severity
        self.event_text = event_text
        self.timestamp = None

    def to_dict(self):
        return {'timestamp': self.timestamp,
                'user_id': self.user_id,
                'client_ip': self.client_ip,
                'severity': self.severity,
                'event_text': self.event_text}

    def __str__(self):
        return str(self.timestamp) \
             + ', ' + self.severity + '/' + self.user_id \
             + ': ' + self.event_text

    '''
    Returns a list of events that match the given search terms.
    '''
    @classmethod
    def list(cls, conn, limit, offset=0, **kwargs):
        with closing(conn.cursor()) as cursor:
            sql = 'SELECT * FROM ' + cls.__name__.lower()
            order = 'timestamp DESC'
            return _selectmany(cursor, cls, sql, order, limit, offset, kwargs)

    '''
    Adds a new event to the database, returns a new Event object.
    '''
    @classmethod
    def new(cls, conn, user_id, client_ip, severity, *event_text):
        event_text = safe_str(*event_text)
        query = "INSERT INTO event (user_id, client_ip, severity, event_text) VALUES (?, ?, ?, ?)"
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (user_id, client_ip, severity, event_text))
            conn.commit()
            return Event(cursor.lastrowid, user_id, client_ip, severity, event_text)

def connect(filename):
    db = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db

def init(conn):
    initial_sql = ''.join(o.init_sql for o in (Config, User, Session, Action, Tag, Event))
    with conn:
        conn.executescript(initial_sql)
        conn.commit()

def close(conn):
    conn.close()

if __name__ == '__main__':
    import os
    os.remove('test.db')
    db = connect('test.db')
    init(db)
    user = User.new(db, 'knipknap@gmail.com', 'Samuel Abels', 'test', True)
    assert user.id is not None
    assert user.is_authorized()
    assert user.check_password('test')
    assert not user.check_password('test2')
    assert User.list(db, 10)[0].id == user.id
    assert User.list(db, 10)[0].email == user.email
    assert User.list(db, 10)[0].full_name == user.full_name
    user.remove(db)
    assert user.id is None
    assert not user.is_authorized()
    assert User.list(db, 10) == []
    assert Action.get(db, id=1).name == 'Open main entry'
    assert Action.get(db, id=2).name == 'Open apartment door'
    tag = Tag.new(db, '04CFF76A873380', 1)
    assert tag.id is not None
    assert Tag.get(db, id='04CFF76A873380').action_id == 1
    db.close()
