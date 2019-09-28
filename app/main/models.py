from app.base_models import BaseModel
from app import db
import random
import datetime
import timeago
import uuid

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

class ContentProvider(BaseModel):
    __tablename__ = "ContentProvider"
    name = db.Column(db.String(20), nullable=False)

class ContentItem(BaseModel):
    __tablename__ = "ContentItem"       
    title = db.Column(db.Text())        
    data = db.Column(db.Text())
    content_tags = db.relationship('ContentTag', secondary=content_tags, backref='ContentItem')        
    content_hash = db.Column(db.String(128), unique=True)    
    contentprovider_id = db.Column(db.Integer, db.ForeignKey('ContentProvider.id'), default=1)    

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

class ContentItemInteraction(BaseModel):
    __tablename__ = 'ContentItemInteraction'    
    contentitem_id = db.Column(db.Integer, db.ForeignKey('ContentItem.id'))
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(50))
    message_id = db.Column(db.Integer)
    data = db.Column(db.String(60))
    trace = db.Column(db.String(256))
    choice = db.Column(db.Integer)
    
    @staticmethod
    def get_interaction_by_id_and_user(message_id, user_id):
        return ContentItemInteraction.query.filter(ContentItemInteraction.message_id==message_id and ContentItemInteraction.user_id==user_id).first()        

    @staticmethod
    def delete_interaction_by_id_and_user(message_id, user_id):
        ContentItemInteraction.query.filter(ContentItemInteraction.message_id==message_id and ContentItemInteraction.user_id==user_id).delete()        
    
    @staticmethod
    def get_interaction_stats(message_id):
        interaction_stats = db.engine.execute(f"""select message_id, choice, count(choice) cnt from ContentItemInteraction 
                                group by message_id, choice
                                having message_id = {message_id}; """)
        return [{'message_id':x[0], 'choice':x[1], 'count':x[2]} for x in interaction_stats]        
    
    @staticmethod
    def add_interaction(**kwargs):
        ci = ContentItemInteraction()
        ci.contentitem_id = kwargs['contentitem_id']
        ci.user_id = kwargs['user_id']
        ci.user_name = kwargs['user_name']
        ci.data = kwargs['data']        
        ci.message_id = kwargs['message_id']     
        ci.choice = kwargs['choice']
        if 'trace' in kwargs:
            ci.trace = kwargs['trace']
        ci.save_to_db()

class ContentItemStat(BaseModel):
    __tablename__ = 'ContentItemStat'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contentitem_id = db.Column(db.Integer, db.ForeignKey('ContentItem.id'))

    @staticmethod
    def get_top_stats(limitby=10):
        now = datetime.datetime.now() + datetime.timedelta(seconds = 60 * 3.4)    
        reddit_content_count = db.engine.execute("""select  LOWER(ContentTag.name), count(*) cnt, max(ci.created_on) from ContentItem ci
        join contenttag_associations on contentitem_id=ci.id 
        join ContentTag on ContentTag.id=contenttag_associations.contenttag_id 
        where ContentTag.name not like '\\_%%'
        group by contenttag_id order by cnt desc, ContentTag.name limit """ + "{};".format(limitby))
        return {x[0]:{'count':x[1], 'last_updated':timeago.format(x[2], now)} for x in list(reddit_content_count)}     
    
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
    plugin_id = db.Column(db.Integer, default=1)
    
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
    chat_id = db.Column(db.String(20), nullable=False)
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
    def create_or_return(cls, key, value):
        kv = KeyValueEntry.query.filter_by(key_id = key.id,value = value).first()        
        if not kv:            
            kv = KeyValueEntry()
            kv.key_id = key.id
            kv.value = value
            kv.save_to_db()
        return kv

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('bot_quote.id'))    

    @classmethod
    def add_statistic(cls, user, quote):
        cs = ContentStats()
        cs.user_id = user.id
        cs.quote_id = quote.id
        cs.save_to_db()

class UserSubscription(BaseModel):
    __tablename__ = 'user_subscriptions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship('User', backref='user_subscriptions')
    keyvalue_entry_id = db.Column(db.Integer, db.ForeignKey('keyvalue_entry.id'))
    keyvalue_entry = db.relationship('KeyValueEntry', backref='user_subscriptions')
    user = db.relationship('User', backref='user_subscriptions')
    
    @classmethod
    def is_user_subscribed_to_key(cls, user_id, key_id):
        r = UserSubscription.query.filter_by(user_id = user_id, keyvalue_entry_id = key_id).first()    
        return r is not None
    @classmethod
    def get_by_id_for_user(cls, id,user_id):
        return UserSubscription.query.filter_by(id=id, user_id=user_id).first()
    @classmethod
    def create_subscription(cls, user_id, topic):
        key = Key.find_by_name('sr_media') #legacy
        kv = KeyValueEntry.create_or_return(key, topic)                
        sub = UserSubscription.is_user_subscribed_to_key(user_id, kv.id)
        if not sub:                        
            subs = UserSubscription()
            subs.user_id = user_id
            subs.keyvalue_entry_id = kv.id
            subs.save_to_db()                          
    @classmethod
    def get_by_user(cls, user_id):
        return UserSubscription.query.join(KeyValueEntry).filter(UserSubscription.user_id==user_id).order_by(KeyValueEntry.value)    
    def __repr__(self):
        return "<UserSubscription {} - {}>".format(self.id, self.keyvalue_entry.value)       



