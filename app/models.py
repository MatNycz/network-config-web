from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  

class User(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    status = db.Column(db.String(8), nullable=False )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Interface(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)  # np. eth0, wlan0
    ipv4 = db.Column(db.String(16))
    ipv6 = db.Column(db.String(16))
    mask = db.Column(db.String(32))
    
    device = db.relationship('Device', backref=db.backref('interfaces', lazy=True))