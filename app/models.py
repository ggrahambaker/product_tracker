from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(64), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    prospect_assets = db.relationship('FinAsset', backref='owner', lazy='dynamic')


    def __repr__(self):
        return('<User: {}, email: {}>'.format(self.username, self.email))

class FinAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(140))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<FinAsset: {}, Owner: {}>'.format(self.name, self.owner.name)