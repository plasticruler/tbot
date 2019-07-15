# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import ArrowType, auto_delete_orphans
from sqlalchemy.sql import func
from sqlalchemy.orm import load_only, relationship
from sqlalchemy.exc import SQLAlchemyError

from passlib.hash import pbkdf2_sha256 as sha256
import random
import datetime

from app import db, log
from app.base_models import BaseModel

    
def generate_random_confirmation_code(length = 10):
    letters = "ABCDEF23456789HJKMNPQRSTUVXYZp@es"
    return ''.join((random.choice(letters) for i in range(length)))

# https://stackoverflow.com/questions/21292726/how-to-properly-use-association-proxy-and-ordering-list-together-with-sqlalchemy
tags = db.Table('tag_associations',
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                db.Column('bot_quote_id', db.Integer, db.ForeignKey('bot_quote.id')))


class Tag(BaseModel):
    __tablename__ = 'tag'
    name = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, name=None):
        self.is_active = True
        self.name = name

    @classmethod
    def find_or_create_tag(cls, name):
        t = Tag.query.filter(Tag.name == name).first()
        if t is None:
            t = Tag(name=name)
        return t

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()


class Bot_Quote(BaseModel):
    __tablename__ = 'bot_quote'
    tags = db.relationship('Tag', secondary=tags, backref='bot_quote')
    text = db.Column(db.String(500))
    content_hash = db.Column(db.String(128)) #the hash of the content item
    
    @classmethod
    def return_random_by_tags(cls, tag_list):
        if tag_list is None or tag_list is []:
            return return_random()
        rowCount = db.session.query(Bot_Quote).join(Tag, Bot_Quote.tags).filter(Tag.name.in_(tag_list)).count()
        return Bot_Quote.query.join(Tag, Bot_Quote.tags).filter(Bot_Quote.is_active == True, Tag.name.in_(tag_list)).offset(int(rowCount*random.random())).first()
    
    @classmethod
    def return_random(cls):        
        rowCount = cls.query.count()
        return cls.query.filter(Bot_Quote.is_active == True).offset(int(rowCount*random.random())).first()

    

    def __repr__(self):
        return '<Bot_Quote {}>'.format(self.text)


class Bot_MessageInbound(BaseModel):
    __tablename__ = 'messages_inbound'
    content = db.Column(db.String(2048))

    def __repr__(self):
        return '<Bot_MessageInbound {}>'.format(self.content)


class Face(BaseModel):
    __tablename__ = 'faces'
    face_encoding = db.Column(db.String(5000))
    person_name = db.Column(db.String(100))

    def __repr__(self):
        return '<Face {}>'.format(self.person_name)


class ImageFile(BaseModel):
    __tablename__ = 'image_file'
    picture_file = db.Column(db.String(512))

    def __repr__(self):
        return '<ImageFile {}>'.format(self.picture_file)


class SelfLog(BaseModel):
    __tablename__ = 'log_self'
    chat_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(512))

    def __repr__(self):
        return "<SelfLog {}>".format(chat_id)


class EquityInstrument(BaseModel):
    __tablename__ = 'equity_instrument'
    jse_code = db.Column(db.String(8), unique=True)
    company_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    prices = db.relationship(
        'EquityPrice', backref='equity_instrument', lazy=True)

    @classmethod
    def find_by_code(cls, code):
        return EquityInstrument.query.filter_by(jse_code=code).first()

    def __repr__(self):
        return '<EquityInstrument {} - {}>'.format(self.jse_code, self.company_name)


class EquityPriceDTO:
    def __init__(self, equityprice):
        self.last_sales_price = equityPrice.last_sales_price
        last_sales_price = equityprice.last_sales_price
        buy_offer_price = equityprice.buy_offer_price
        sell_offer_price = equityprice.sell_offer_price
        last_sales_price = equityprice.last_sales_price
        price_move = equityprice.price_move
        volume_count = equityprice.volume_count
        deal_count = equityprice.deal_count
        deals_value = equityprice.deals_value
        today_high = equityprice.today_high
        today_low = equityprice.today_low
        from_52_week_high = equityprice.from_52_week_high
        from_52_week_low = equityprice.from_52_week_low
        downloaded_timestamp = equityprice.downloaded_time_stamp
        equitypricesource_id = equityprice.equitypricesource_id
        equityinstrument_id = equityprice.equityinstrument_id


class EquityPrice(BaseModel):
    __tablename__ = 'equity_price'
    last_sales_price = db.Column(db.Integer, nullable=False)
    buy_offer_price = db.Column(db.Integer, nullable=False)
    sell_offer_price = db.Column(db.Integer, nullable=False)
    last_sales_price = db.Column(db.Integer, nullable=False)
    price_move = db.Column(db.Float(5), nullable=False)
    volume_count = db.Column(db.Integer, nullable=False)
    deal_count = db.Column(db.Integer, nullable=False)
    deals_value = db.Column(db.Integer, nullable=False)
    today_high = db.Column(db.Integer, nullable=False)
    today_low = db.Column(db.Integer, nullable=False)
    from_52_week_high = db.Column(db.Integer, nullable=False)
    from_52_week_low = db.Column(db.Integer, nullable=False)
    downloaded_timestamp = db.Column(db.DateTime, nullable=False)
    equitypricesource_id = db.Column(db.Integer, db.ForeignKey(
        'equity_price_source.id'), nullable=False)
    equityinstrument_id = db.Column(db.Integer, db.ForeignKey(
        'equity_instrument.id'), nullable=False)
    equitypricesource = db.relationship(
        'EquityPriceSource', backref='equity_price', lazy=True)
    equityinstrument = db.relationship(
        'EquityInstrument', backref='equity_price', lazy=True)
    interval = db.Column(db.Integer, default=1)

    @classmethod
    def get_last_sales_prices_by_date(cls, share_code, dt):
        return [EquityPriceDTO(x) for x in EquityPrice.query.filter(EquityPrice.downloaded_timestamp >= dt and EquityPrice.downloaded_timestamp<= (dt + datetime.timedelta(days=1))).filter(EquityPrice.equityinstrument_id == EquityInstrument.find_by_code(share_code).id)]

    def __repr__(self):
        return '<EquityPrice {} - {}>'.format(self.equityinstrument.jse_code, self.last_sales_price)


class EquityPriceSource(BaseModel):
    __tablename__ = 'equity_price_source'
    source_name = db.Column(db.String(50), unique=True, nullable=False)
    source_key = db.Column(db.String(10), unique=True)
    data1 = db.Column(db.String(100))
    data2 = db.Column(db.String(100))
    data3 = db.Column(db.String(100))
    data4 = db.Column(db.String(100))
    data5 = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

    @classmethod
    def find_by_source_key(cls, source_key):
        return EquityPriceSource.query.filter_by(source_key=source_key).first()

    def __repr__(self):
        return '<EquityPriceSource {}>'.format(self.source_name)


class Key(BaseModel):
    __tablename__ = 'key'
    name = db.Column(db.String(20), nullable=False, unique=True)

    @classmethod
    def find_by_name(cls, name):
        return Key.query.filter_by(name=name).first()

    def __repr__(self):
        return '<Key {}>'.format(self.name)

class KeyValueEntry(BaseModel):
    __tablename__ = 'keyvalue_entry'
    __table_args__ = (db.UniqueConstraint('key_id','value',name='unique_key_value'),)
    key = db.relationship(
        'Key', backref='keyvalue_entry', lazy=True)
    key_id = db.Column(db.Integer, db.ForeignKey(
        'key.id'), nullable=False)
    value = db.Column(db.String(50), nullable=False)

    @classmethod
    def find_by_key_value(cls, key, value):
        k = Key.find_by_name(key)
        if k is None:
            return None
        return KeyValueEntry.query.filter_by(key_id=k.id, value=value).first()

    @classmethod
    def get_by_key(cls, key):
        k = Key.find_by_name(key)
        if k is None:
            return None
        return KeyValueEntry.query.filter_by(key_id=k.id)   

    def __repr__(self):
        return '<KeyValueEntry {}-{}>'.format(self.key.name, self.value)
class ContentStats(BaseModel):
    __tablename__ = 'content_stats'
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    quote_id = db.Column(db.Integer(), db.ForeignKey('bot_quote.id'))

    @classmethod
    def add_statistic(cls, user, quote):
        cs = ContentStats()
        cs.user_id = user.id
        cs.quote_id = quote.id
        cs.save_to_db()

class Role(BaseModel):
    __tablename__ = 'roles'
    name = db.Column(db.String(30), unique=True)
class UserRole(BaseModel):
    __tablename__ = 'user_roles'
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    roles_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class UserSubscription(BaseModel):
    __tablename__ = 'user_subscriptions'
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    content_id = db.Column(db.Integer(), db.ForeignKey('keyvalue_entry.id'))
    content = db.relationship('KeyValueEntry', backref='user_subscriptions')
    user = db.relationship('User', backref='user_subscriptions')
    @classmethod
    def get_by_id_for_user(cls, id, user_id):
        return UserSubscription.query.filter(UserSubscription.user_id==user_id and UserSubscription.content_id==id).first()
    @classmethod
    def get_by_user(cls, user_id):
        return UserSubscription.query.filter(UserSubscription.user_id==user_id)
    def __repr__(self):
        return "<UserSubscription user_id: {} content_id: {}".format(self.user, self.content_id)
    
    @classmethod
    def get_by_user(cls, user_id):
        return UserSubscription.query.filter(UserSubscription.user_id==user_id)
class User(UserMixin, BaseModel):
    __tablename__ = "users"
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=False)
    roles = db.relationship("Role", secondary="user_roles")
    confirmation_code = db.Column(db.String(10), default=generate_random_confirmation_code())
    chat_id = db.Column(db.Integer())
    subscriptions_active = db.Column(db.Boolean, default=False)
    last_seen_ip_address = db.Column(db.String(128))

    def __repr__(self):
        return "<User: {} {}>".format(self.id, self.email)
    
    def add_sub(self,sub):
        kvn = sub.strip()
        k = 'sr_media' #always assume it's media related        
        key = Key.find_by_name(k)
        if (key is None):
            key = Key()
            key.name = k
            key.save_to_db()
        kv = KeyValueEntry.find_by_key_value(k, kvn)
        if kv is None:            
            kv = KeyValueEntry()
            kv.key = key
            kv.value = kvn
            kv.save_to_db()
        sub = UserSubscription()
        sub.user_id = self.id
        sub.content_id = kv.id
        sub.save_to_db()  

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first() 
    @classmethod
    def find_by_chatid(cls, chatid):
        return cls.query.filter_by(chat_id=chatid).first() 

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

# auto
# auto_delete_orphans(Bot_Quote._tags)
