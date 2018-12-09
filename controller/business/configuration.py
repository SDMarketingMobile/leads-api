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

@get('/configurations')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		query_set = Configuration.objects().filter()

		if 'key' in url_params['params']:
			query_set = query_set.filter(key = url_params['params']['key'])

		return query_set.to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@post('/configuration')
def new():
	try:
		# load data from post
		post_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		config = Configuration()
		config.key 		= post_data['key']
		config.value 	= post_data['value']
		config.save()

		response.status = 201
		response.headers['Content-Type'] = 'application/json'
		return config.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)