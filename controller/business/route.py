# -*- coding: utf-8 -*-
import json, bcrypt, base64, os, sys, jsonpickle
from os import path
from bottle import request, response
from bottle import get, put, post, delete
from bson import ObjectId
from bson import DBRef
from mongoengine import *
from ..model.models import *
from ..util.utils import *
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

@get('/route/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return Route.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/routes')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		query_set = Route.objects(deleted = False).filter()

		if 'departure_date' in url_params['params']:
			query_set = query_set.filter(departure_date = url_params['params']['departure_date'])

		if 'arrival_date' in url_params['params']:
			query_set = query_set.filter(arrival_date = url_params['params']['arrival_date'])

		if 'line_id' in url_params['params']:
			query_set = query_set.filter(
				line = DBRef('lines', ObjectId(url_params['params']['line_id']))
			)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			result = query_set.to_json()
		else:
			result = PaginationUtil().paginate(query_set, url_params['offset'], url_params['limit'])
		
		if (not (result is None)):
			response.headers['Content-Type'] = 'application/json'
			return result
		else:
			response.status = 404
			return 'Nenhum registro encontrado'
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@post('/route')
def new(data=None):
	try:
		if data is None:
			post_data = jsonpickle.decode(request.body.read().decode('utf-8'))
		else:
			post_data = data

		route = Route()
		route.line 				= DBRef('lines', ObjectId(post_data['line']['id']))
		route.departure_date 	= parse(post_data['departure_date'])
		route.arrival_date 		= parse(post_data['arrival_date'])
		route.save()

		response.status = 201
		response.headers['Content-Type'] = 'application/json'
		return route.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/route/<id:re:[0-9a-f]{24}>')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		route = Route.objects(id = id)

		route.update_one(
			line 			= DBRef('lines', ObjectId(request_data['line']['id'])),
			departure_date 	= request_data['departure_date'],
			arrival_date 	= request_data['arrival_date']
		)

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return route.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)		

@delete('/route/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		Route.objects(
			id = id
		).update(
			deleted = True,
			deleted_at = datetime.datetime.now()
		)
		response.status = 200
		return 'Registro excluido com sucesso!'
	except Exception as e:
		response.status = 500
		return str(e)