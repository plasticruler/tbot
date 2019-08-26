from app import db
from app.base_models import BaseModel
from app.utils import generate_random_confirmation_code
from passlib.hash import pbkdf2_sha256 as sha256
from flask_security import UserMixin, RoleMixin



roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))

class Role(BaseModel, RoleMixin):
    __tablename__ = 'roles'
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(250))
    def __repr__(self):
        return self.name

class User(BaseModel, UserMixin):
    __tablename__ = "users"
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    confirmation_code = db.Column(db.String(10), default=generate_random_confirmation_code())
    chat_id = db.Column(db.Integer(), unique=True)
    subscriptions_active = db.Column(db.Boolean, default=False)
    last_seen_ip_address = db.Column(db.String(128))
    note = db.Column(db.String(200))
    utc_offset = db.Column(db.Integer())
    bot_id = db.Column(db.Integer(), default=1, nullable=False)
    user_type = db.Column(db.Integer(), default=1, nullable=False) #1 = user, 2 = channel
    over_18_allowed = db.Column(db.Boolean, default=False)
    over_18_last_accepted = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<User: {} {}>".format(self.id, self.email)        

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first() 

    @classmethod
    def find_by_chatid(cls, chatid):
        return cls.query.filter_by(chat_id=chatid).first() 
    
    @classmethod
    def exists(cls,**kwargs):
        return cls.query.filter_by(**kwargs).count()==1

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @staticmethod
    def create_user(email, plaintext_password, chat_id=0):
        n = User()
        n.email = email
        n.password = User.generate_hash(plaintext_password)
        n.chat_id = chat_id
        n.save_to_db()
        return n
