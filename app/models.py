# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import ArrowType, auto_delete_orphans
from sqlalchemy.sql import func
from sqlalchemy.orm import load_only
from sqlalchemy.exc import SQLAlchemyError

from passlib.hash import pbkdf2_sha256 as sha256
import random
import datetime

from app import db, log

# https://stackoverflow.com/questions/21292726/how-to-properly-use-association-proxy-and-ordering-list-together-with-sqlalchemy
tags = db.Table('tag_associations',
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                db.Column('bot_quote_id', db.Integer, db.ForeignKey('bot_quote.id')))


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            log.error(str(e))
            db.session.rollback()


class Tag(BaseModel):
    __tablename__ = 'tag'
    name = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, name=None):
        self.is_active = True
        self.name = name

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {'name': x.name, 'active': x.is_active}

        return {'tags': list(map(lambda x: to_json(x), Tag.query.all()))}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()


class Bot_Quote(BaseModel):
    __tablename__ = 'bot_quote'
    _tags = db.relationship('Tag', secondary=tags, backref='bot_quote')
    tag_list = association_proxy('_tags', 'name')
    text = db.Column(db.String(500))
    content_hash = db.Column(db.String(128)) #the hash of the content item

    @property
    def tags(self):
        tag_list = getattr(self, 'tag_list', [])
        return tag_list if (tag_list != ['']) else []

    @tags.setter
    def tags(self, tag_list):
        self._tags = [self.find_or_create_tag(t) for t in tag_list]

    @classmethod
    def return_random(cls):        
        rowCount = int(cls.query.count())
        return cls.query.filter(Bot_Quote.is_active == True).offset(int(rowCount*random.random())).first()

    def find_or_create_tag(self, name):
        t = Tag.query.filter(Tag.name == name).first()
        if t is None:
            t = Tag(name=name)
        return t
    

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

    @classmethod
    def to_json(cls, x):
        return {'content': x.message, 'chat_id': self.chat_id}

    @classmethod
    def return_all(cls):
        return {'selflogs': list(map(lambda x: SelfLog.to_json(x), SelfLog.query.all()))}

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
    def to_json(cls, x):
        return {'company_name': x.company_name, 'jse_code': x.jse_code, 'is_active': x.is_active}

    @classmethod
    def return_all(cls):
        return {'instruments': list(map(lambda x: EquityInstrument.to_json(x), EquityInstrument.query.all()))}

    @classmethod
    def find_by_code(cls, code):
        return EquityInstrument.query.filter_by(jse_code=code).first()

    @classmethod
    def return_tracked(cls):
        return {'instruments': list(map(lambda x: x.jse_code, EquityInstrument.query.filter_by(is_active=True)))}

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
    name = db.Column(db.String(20), nullable=False)

    @classmethod
    def find_by_name(cls, name):
        return Key.query.filter_by(name=name).first()

    def __repr__(self):
        return '<Key {}>'.format(self.name)

class KeyValueEntry(BaseModel):
    __tablename__ = 'keyvalue_entry'
    key = db.relationship(
        'Key', backref='value_entries', lazy=True)
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

class User(UserMixin, BaseModel):
    __tablename__ = "users"
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    roles = db.relationship("Role", secondary="user_roles")
    subscriptions = db.relationship("KeyValueEntry", secondary = "user_subscriptions")
    confirmation_code = db.Column(db.String(10))
    chat_id = db.Column(db.Integer())

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()    
    
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

# auto
# auto_delete_orphans(Bot_Quote._tags)
