from app import db, login
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import jwt
from time import time
from app.search import add_to_index, remove_from_index, query_index
import json


followers = db.Table(
    'followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('asset_id', db.Integer, db.ForeignKey('fin_asset.id'))
)



class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(64), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    prospect_assets = db.relationship('FinAsset', backref='owner', lazy='dynamic')
    comments = db.relationship('FinComment', backref='author', lazy='dynamic')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')

    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'FinAsset', secondary=followers,
        backref = 'users', 
        lazy='dynamic')

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    def follow_asset(self, asset):
        if not self.is_following(asset):
            self.followed.append(asset)
    
    def unfollow_asset(self, asset):
        if self.is_following(asset):
            self.followed.remove(asset)

    def is_following(self, asset):
        return self.followed.filter(
            followers.c.asset_id == asset.id
        ).count() > 0

    def get_followed_assets(self):
        return self.followed

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


    def __repr__(self):
        return('<User: {}, email: {}>'.format(self.username, self.email))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class FinAsset(SearchableMixin, db.Model):
    __searchable__ = ['description', 'name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('FinComment', backref='asset', lazy='dynamic')
    followed_by = db.relationship(
        'User', secondary=followers,
        backref = 'assets', 
        lazy = 'dynamic')
    
    def get_followers(self):
        return FinAsset.followed_by

    

    ## need to make url routing for weird names for asset names

    
class FinComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    asset_id = db.Column(db.Integer, db.ForeignKey('fin_asset.id'))
    body = db.Column(db.String(600))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)




class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


