from app.base_models import BaseModel
from app import db
import random
import datetime

# https://stackoverflow.com/questions/21292726/how-to-properly-use-association-proxy-and-ordering-list-together-with-sqlalchemy
tags = db.Table('tag_associations',
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                db.Column('bot_quote_id', db.Integer, db.ForeignKey('bot_quote.id')))

content_tags = db.Table('contenttag_associations',
        db.Column('contenttag_id', db.Integer, db.ForeignKey('ContentTag.id')),
        db.Column('contentitem_id', db.Integer, db.ForeignKey('ContentItem.id')))        

class Notification(BaseModel):
    __tablename__ = "Notification"
    title = db.Column(db.Text())
    text = db.Column(db.Text())
    category_id = db.Column(db.Integer)
    active_from = db.Column(db.DateTime, default=datetime.datetime.now)

class ContentItem(BaseModel):
    __tablename__ = "ContentItem"   
    providerid = db.Column(db.String(6), nullable=True) 
    title = db.Column(db.Text())    
    data = db.Column(db.Text())
    content_tags = db.relationship('ContentTag', secondary=content_tags, backref='ContentItem')        
    content_hash = db.Column(db.String(128), unique=True)

    @classmethod
    def return_random_by_tags(cls, tag_list):
        if tag_list is None or tag_list is []:
            return return_random()
        rowCount = db.session.query(ContentItem).join(ContentTag, ContentItem.content_tags).filter(ContentTag.name.in_(tag_list)).count()
        return ContentItem.query.join(ContentTag, ContentItem.content_tags).filter(ContentItem.is_active == True, ContentTag.name.in_(tag_list)).offset(int(rowCount*random.random())).first()
    @classmethod
    def return_by_tag(cls, tag):
        if tag is None or tag is []:
            raise Exception("Empty tag_list")
        return ContentItem.query.join(ContentTag, ContentItem.content_tags).filter(ContentItem.is_active == True, ContentTag.name == tag)

    @classmethod
    def return_random(cls):        
        rowCount = cls.query.count()
        return cls.query.filter(ContentItem.is_active == True).offset(int(rowCount*random.random())).first()

    def __repr__(self):
        return '<ContentItem {}>'.format(self.title)

class ContentItemStat(BaseModel):
    __tablename__ = 'ContentItemStat'
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    contentitem_id = db.Column(db.Integer(), db.ForeignKey('ContentItem.id'))
    
    @classmethod
    def add_statistic(cls, user, quote):
        cs = ContentItemStat()
        cs.user_id = user.id
        cs.contentitem_id = quote.id
        cs.save_to_db()

class Bot_Quote(BaseModel):
    __tablename__ = 'bot_quote'
    tags = db.relationship('Tag', secondary=tags, backref='bot_quote')
    text = db.Column(db.String(500))
    content_hash = db.Column(db.String(128)) #the hash of the content item
    plugin_id = db.Column(db.Integer(), default=1)
    
    @classmethod
    def return_random_by_tags(cls, tag_list):
        if tag_list is None or tag_list is []:
            return return_random()
        rowCount = db.session.query(Bot_Quote).join(Tag, Bot_Quote.tags).filter(Tag.name.in_(tag_list)).count()
        return Bot_Quote.query.join(Tag, Bot_Quote.tags).filter(Bot_Quote.is_active == True, Tag.name.in_(tag_list)).offset(int(rowCount*random.random())).first()
    @classmethod
    def return_by_tag(cls, tag):
        if tag is None or tag is []:
            raise Exception("Empty tag_list")
        return Bot_Quote.query.join(Tag, Bot_Quote.tags).filter(Bot_Quote.is_active == True, Tag.name == tag)

    @classmethod
    def return_random(cls):        
        rowCount = cls.query.count()
        return cls.query.filter(Bot_Quote.is_active == True).offset(int(rowCount*random.random())).first()

    def __repr__(self):
        return '<Bot_Quote {}>'.format(self.text)

class ContentTag(BaseModel):
        __tablename__ = 'ContentTag'
        name = db.Column(db.String(120), unique=True, nullable=False)
    
        def __init__(self, name=None):
            self.is_active = True
            self.name = name
    
        @classmethod
        def find_or_create_tag(cls, name):
            t = ContentTag.query.filter(ContentTag.name == name).first()
            if t is None:
                t = ContentTag(name=name)
            return t
    
        @classmethod
        def find_by_name(cls, name):
            return cls.query.filter_by(name=name).first()

class Tag(BaseModel):
    __tablename__ = 'tag'
    name = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return "<{} - {}>".format(self.name, self.id)

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

class Bot_MessageInbound(BaseModel):
    __tablename__ = 'messages_inbound'
    content = db.Column(db.String(2048))

    def __repr__(self):
        return '<Bot_MessageInbound {}>'.format(self.content)

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

class UserSubscription(BaseModel):
    __tablename__ = 'user_subscriptions'
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    content_id = db.Column(db.Integer(), db.ForeignKey('keyvalue_entry.id'))
    content = db.relationship('KeyValueEntry', backref='user_subscriptions')
    user = db.relationship('User', backref='user_subscriptions')
    @classmethod
    def get_by_id_for_user(cls, id, user_id):
        return UserSubscription.query.filter_by(id=id).filter_by(user_id=user_id).first()
    @classmethod
    def get_by_user(cls, user_id):
        return UserSubscription.query.join(KeyValueEntry).filter(UserSubscription.user_id==user_id).order_by(KeyValueEntry.value)
    def __repr__(self):
        return "{}".format(self.content.value)        


