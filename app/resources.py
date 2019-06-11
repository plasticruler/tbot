# coding: utf-8
from flask_restful import Resource, reqparse
from flask_restful.utils import cors
from app.models import Tag, Bot_Quote, EquityInstrument, KeyValueEntry
from app import log, db
import json


class BaseResource(Resource):
    def get_parser(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'username', 'this field cannot be blank', location='headers', required=True)
        parser.add_argument(
            'password', 'this field cannot be blank', location='headers', required=True)
        return parser

    def options(self):
        return {'Allow': 'GET'}, 200, {'Access-Control-Allow-Origin': '*',  'Access-Control-Allow-Methods': 'PUT,GET'}


class EquityInstrumentResource(BaseResource):
    def get(self):
        parser = self.get_parser()
        parser.add_argument('code')
        params = parser.parse_args()
        if params['code'] is None:
            return EquityInstrument.return_all()
        else:
            ei = EquityInstrument.find_by_code(params['code'])
            if ei is not None:
                return EquityInstrument.to_json(ei)
            else:
                return 'Not Found.', 404

class TrackedInstrumentResource(BaseResource):
    def get(self):
        return EquityInstrument.return_tracked()

    def post(self):
        parser = self.get_parser()
        parser.add_argument(
            'codes', 'this field cannot be blank', required=True)
        data = parser.parse_args()        
        for code in data['codes'].split(','):
            EquityInstrument.query.filter_by(
                jse_code=code).update(dict(is_active=True))
        db.session.commit()
        return 'Ok'


class TagResource(BaseResource):
    def get(self):
        return Tag.return_all()

    def post(self):
        parser = self.get_parser()
        parser.add_argument(
            'name', 'this field cannot be blank', required=True)
        data = parser.parse_args()
        name = data['name']
        if Tag.find_by_name(name):
            return {'message': 'Tag "{}" already exists.'.format(name)}
        try:
            tag = Tag(name=name, active=True)
            tag.save_to_db()
            return {'message': 'Tag created'}, 201
        except Exception as e:
            log.error(e)
            return{'message': 'Something went wrong.' + e}, 500


class QuoteResource(Resource):
    def get(self):
        return Bot_Quote.return_random()

    def post(self):
        parser = self.get_parser()
        parser.add_argument(
            'quoteText', 'this field cannot be blank', required=True)
        parser.add_argument('tags', '', required=False)
        data = parser.parse_args()
        quote_text = data['quoteText']
        tags = []
        try:
            quote = Bot_Quote(text=quote_text)
            quote.save_to_db()
            return {'message': 'Quote created'}, 201
        except Exception as e:
            log.error(e)
            return {'message': 'Something went wrong. ' + e}, 500
