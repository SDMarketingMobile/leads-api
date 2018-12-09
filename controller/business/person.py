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

@get('/person/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return Person.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/person')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = Person.objects(deleted = False).filter()

		if 'type' in url_params['params']:
			query_set = query_set.filter(type = url_params['params']['type'])

		if 'filter' in url_params['params']:
			query_set = query_set.filter(
				Q(plate_number__icontains = url_params['params']['filter'])
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

@post('/person')
def new(data=None):
	try:
		if not(data is None):
			post_data = data
		else:
			# load data from post
			post_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		person_exists = None

		try:
			person_exists = Person.objects(
				rg = post_data['rg']
			).get()

			if not (person_exists is None):
				if not(data is None):
					return person_exists
				else:
					response.status = 406
					return 'Já existe um passageiro cadastrado com este RG!'
		except DoesNotExist as e:
			pass

		try:
			person_exists = Person.objects(
				cpf = post_data['cpf']
			).get()

			if not (person_exists is None):
				if not(data is None):
					return person_exists
				else:
					response.status = 406
					return 'Já existe um passageiro cadastrado com este RG!'
		except DoesNotExist as e:
			pass

		person = Person()
		person.gender 			= post_data['gender']
		person.first_name 		= post_data['first_name']
		person.last_name 		= post_data['last_name']
		person.rg 				= post_data['rg']
		person.cpf				= post_data['cpf']
		person.birth_date		= post_data['birth_date']
		person.save()

		if not(data is None):
			return person
		else:
			response.status = 201
			response.headers['Content-Type'] = 'application/json'
			return person.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/person/<id:re:[0-9a-f]{24}>')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		person = Person.objects(id = id)

		person.update_one(
			gender 		= request_data['gender'],
			first_name 	= request_data['first_name'],
			last_name 	= request_data['last_name'],
			rg 			= request_data['rg'],
			cpf 		= request_data['cpf'],
			birth_date 	= request_data['birth_date']
		)

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return person.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@delete('/person/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		Person.objects(
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