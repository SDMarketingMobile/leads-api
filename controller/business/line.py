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

		if 'profile' in url_params['params']:
			query_set = query_set.filter(profile = url_params['params']['profile'])

		if 'city_origin' in url_params['params']:
			query_set = query_set.filter(
				Q(city_origin__icontains = url_params['params']['city_origin'])
			)

		if 'city_destiny' in url_params['params']:
			query_set = query_set.filter(
				Q(city_destiny__icontains = url_params['params']['city_destiny'])
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
		line.vehicle 		= DBRef('vehicles', ObjectId(post_data['vehicle']['id']))
		line.state_origin	= post_data['state_origin']
		line.city_origin	= post_data['city_origin']
		line.state_destiny	= post_data['state_destiny']
		line.city_destiny	= post_data['city_destiny']
		line.person_price	= post_data['person_price']
		line.save()

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
			vehicle 		= DBRef('vehicles', ObjectId(request_data['vehicle']['id'])),
			state_origin 	= request_data['state_origin'],
			city_origin 	= request_data['city_origin'],
			state_destiny 	= request_data['state_destiny'],
			city_destiny 	= request_data['city_destiny'],
			person_price 	= request_data['person_price']
		)

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