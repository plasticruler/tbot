# coding: utf-8
from flask_sqlalchemy import SQLAlchemy

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

    @property
    def tags(self):
        tag_list = getattr(self, 'tag_list', [])
        return tag_list if (tag_list != ['']) else []

    @tags.setter
    def tags(self, tag_list):
        self._tags = [self.find_or_create_tag(t) for t in tag_list]

    @classmethod
    def return_random(cls):
        def to_json(x):
            return {'quote': x.text, 'id': x.id}
        rowCount = int(cls.query.count())
        return {'quotes': to_json(cls.query.filter(Bot_Quote.is_active == True).offset(int(rowCount*random.random())).first())}

    def find_or_create_tag(self, name):
        t = Tag.query.filter(Tag.name == name).first()
        if t is None:
            t = Tag(name=name)
        return t

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {'quote': x.text, 'id': x.id}
        return {'quotes': list(map(lambda x: to_json(x), Bot_Quote.query.all()))}

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
    prices = db.relationship('EquityPrice', backref='equity_instrument', lazy=True)

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
    equitypricesource_id = db.Column(db.Integer, db.ForeignKey('equity_price_source.id'), nullable=False)
    equityinstrument_id = db.Column(db.Integer, db.ForeignKey('equity_instrument.id'), nullable=False)
    equitypricesource = db.relationship('EquityPriceSource', backref='equity_price', lazy=True)
    equityinstrument = db.relationship('EquityInstrument', backref='equity_price', lazy=True)
    

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

    @classmethod
    def to_json(cls, x):
        return {'kv': x.key.name, 'value': x.value, 'is_active': x.is_active}

    @classmethod
    def return_all(cls):
        return {'keyvalues': list(map(lambda x: KeyValueEntry.to_json(x), EquityInstrument.query.all()))}

    def __repr__(self):
        return '<KeyValueEntry {}-{}>'.format(self.key.name, self.value)


class UserModel(BaseModel):
    __tablename__ = 'users'
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.String(120))

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                "username": x.username,
                "password": x.password
            }
        return {"users": list(map(lambda x: to_json(x), UserModel.query.all()))}

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {"message": "{} rows deleted.".format(num_rows_deleted)}
        except:
            return {"message": "Something went wrong."}

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

# auto
# auto_delete_orphans(Bot_Quote._tags)
