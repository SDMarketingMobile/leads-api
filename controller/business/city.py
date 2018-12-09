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

@get('/cities')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = City.objects().filter()

		if 'filter' in url_params['params']:
			query_set = query_set.filter(
				Q(name__icontains = url_params['params']['filter'])
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