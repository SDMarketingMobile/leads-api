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
from . import route

@get('/line/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return Line.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/lines')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = Line.objects(deleted = False).filter()

		if 'filter' in url_params['params']:
			query_set = query_set.filter(
				origin__name__icontains = DBRef('cities', ObjectId(url_params['params']['filter']))
			)

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

@post('/line')
def new():
	try:
		# load data from post
		post_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		line = Line()
		line.description 	= post_data['description']
		line.vehicle 		= DBRef('vehicles', ObjectId(post_data['vehicle']['id']))
		line.origin			= DBRef('cities', ObjectId(post_data['origin']['id']))
		line.destiny 		= DBRef('cities', ObjectId(post_data['destiny']['id']))
		line.person_price 	= float(post_data['person_price'])
		line.save()

		if not('routes' in post_data):
			response.status = 406
			return 'Você deve informar ao menos uma rota'
		else:
			for item in post_data['routes']:
				if 'deleted' in item and bool(item['deleted']) == False:
					item['line'] = {
						'id': str(line.id)
					}
					route.new(item)

		response.status = 201
		response.headers['Content-Type'] = 'application/json'
		return line.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/line/<id:re:[0-9a-f]{24}>')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		line = Line.objects(id = id)

		line.update_one(
			description 	= request_data['description'],
			vehicle 		= DBRef('vehicles', ObjectId(request_data['vehicle']['id'])),
			origin			= DBRef('cities', ObjectId(request_data['origin']['id'])),
			destiny 		= DBRef('cities', ObjectId(request_data['destiny']['id'])),
			person_price 	= request_data['person_price']
		)

		if not('routes' in request_data):
			response.status = 406
			return 'Você deve informar ao menos uma rota'
		else:
			for item in request_data['routes']:
				if not('id' in item):
					item['line'] = {
						'id': id
					}
					route.new(item)
				elif 'deleted' in item and bool(item['deleted']) == True:
					route.delete(item['id'])

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return line.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)		

@delete('/line/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		Line.objects(
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