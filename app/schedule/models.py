
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm import load_only, relationship
from sqlalchemy.exc import SQLAlchemyError

import random
import datetime

from app import db, log
from app.base_models import BaseModel

class ConfiguredTask(BaseModel):
    __tablename__ = 'configured_task'   
    name = db.Column(db.String(100))     
    minute =  db.Column(db.String(10))
    hour = db.Column(db.String(10))
    day_of_week = db.Column(db.String(50))
    day_of_month = db.Column(db.String(50))
    month_of_year = db.Column(db.String(50))
    task_class = db.Column(db.String(100))
    parameters = db.relationship('Parameter', backref='configured_task', lazy=True)

class Parameter(BaseModel):
    __tablename__ = 'task_parameter'
    name = db.Column(db.String(20))
    value = db.Column(db.String(20))
    is_string = db.Column(db.Boolean, default=True)
    configuredtask_id = db.Column(db.Integer, db.ForeignKey('configured_task.id'))


