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
    is_active = db.Column(db.Boolean, nullable=False, default=True) # New field

    rounds = db.relationship('Round', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} (Active: {self.is_active})>' # Updated repr

class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # New fields
    address = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    registered_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Old field (to be removed)
    # coordinates = db.Column(db.String(100), nullable=True)

    # Relationships
    checkpoints = db.relationship('Checkpoint', backref='site', lazy=True)
    rounds = db.relationship('Round', backref='site', lazy=True)
    access_points = db.relationship('Access', backref='site', lazy=True, cascade="all, delete-orphan")

    # Relationship to get User details of who registered the site
    registered_by = db.relationship('User', foreign_keys=[registered_by_user_id])


    def __repr__(self):
        return f'<Site {self.name} (Lat: {self.latitude}, Lon: {self.longitude})>'

class Access(db.Model):
    __tablename__ = 'access'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
        coordinates = db.Column(db.String(100), nullable=True) # e.g., "latitude,longitude"
        description = db.Column(db.Text, nullable=True)
        point_number = db.Column(db.Integer, nullable=False) # New field
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)

        # Example for unique constraint if point_number should be unique per site
        # __table_args__ = (db.UniqueConstraint('site_id', 'point_number', name='_site_point_uc'),)


    def __repr__(self):
            return f'<Access Point {self.point_number}: {self.name} @ Site {self.site_id}>' # Updated repr

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
