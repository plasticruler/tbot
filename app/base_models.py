from app import db, log
import datetime
from sqlalchemy.exc import SQLAlchemyError

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()            
        except SQLAlchemyError as e:            
            log.error(str(e))
            db.session.rollback()
    def save(self):
        self.save_to_db()
    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            log.error(str(e))
            db.session.rollback()