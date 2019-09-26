from app.base_models import BaseModel
from app.auth.models import User, Role
from app import db
import random
import datetime
import timeago


class Queue(BaseModel):
    __tablename__ = 'Queue'
    name = db.Column(db.String(50), unique=True)

class Interaction(BaseModel):
    __tablename__ = 'Interaction'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)    
    chat_id = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.Integer)

class InteractionMessage(BaseModel):
    __tablename__ = 'InteractionMessage'
    interaction_id = db.Column(db.Integer, db.ForeignKey('Interaction.id'))

class Product(BaseModel):
    __tablename__ = 'Product'
    name = db.Column(db.String(50))    

class ContentItemStat(BaseModel):
    __tablename__ = 'ContentItemStat'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contentitem_id = db.Column(db.Integer, db.ForeignKey('ContentItem.id'))