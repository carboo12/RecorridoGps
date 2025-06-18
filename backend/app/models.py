from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserType(db.Model):
    __tablename__ = 'user_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'admin', 'supervisor'
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship('User', backref='user_type', lazy=True)

    def __repr__(self):
        return f'<UserType {self.name}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    user_type_id = db.Column(db.Integer, db.ForeignKey('user_type.id'), nullable=False)
    # Removed: role = db.Column(db.String(20), nullable=False, default='user')

    rounds = db.relationship('Round', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    coordinates = db.Column(db.String(100), nullable=True) # For "lat,lon" or similar format

    checkpoints = db.relationship('Checkpoint', backref='site', lazy=True)
    rounds = db.relationship('Round', backref='site', lazy=True)
    access_points = db.relationship('Access', backref='site', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Site {self.name}>'

class Access(db.Model):
    __tablename__ = 'access'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    coordinates = db.Column(db.String(100), nullable=True) # For "lat,lon" or similar format
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Access {self.name} for Site {self.site_id}>'

class Checkpoint(db.Model):
    __tablename__ = 'checkpoint'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)

    def __repr__(self):
        return f'<Checkpoint {self.name} @ Site {self.site_id}>'

class Round(db.Model):
    __tablename__ = 'round'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')

    # user relationship is now correctly defined in User model by backref='user'
    round_checkpoints = db.relationship('RoundCheckpoint', backref='round', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Round {self.id} by User {self.user_id} at Site {self.site_id}>'

class RoundCheckpoint(db.Model):
    __tablename__ = 'round_checkpoint'
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    checkpoint_id = db.Column(db.Integer, db.ForeignKey('checkpoint.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    checkpoint = db.relationship('Checkpoint')

    def __repr__(self):
        return f'<RoundCheckpoint {self.id} for Round {self.round_id} at Checkpoint {self.checkpoint_id}>'
