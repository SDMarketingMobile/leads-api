# -*- coding: utf-8 -*-
import json, bcrypt, base64, os, sys, jsonpickle, iugu
from os import path
from bottle import request, response
from bottle import get, put, post, delete
from bson import ObjectId
from bson import DBRef
from mongoengine import *
from ..model.models import *
from ..util.utils import *

@post('/user/login')
def login():
	try:
		post_data = json.loads(request.body.getvalue().decode('utf-8'))
		
		user = User.objects(
			email = post_data['email'],
			profile = post_data['profile'],
			deleted = False
		).get()
		
		if(bcrypt.checkpw(post_data['password'].encode('utf-8'), user.password)):
			response.headers['Content-Type'] = 'application/json'
			return user.to_json()
		else:
			response.status = 406
			return 'Senha inválida.'
	except DoesNotExist as e:
		response.status = 404
		return 'Usuário não encontrado.'

@get('/user/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return User.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/users')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = User.objects(deleted = False).filter()

		if 'profile' in url_params['params']:
			query_set = query_set.filter(profile = url_params['params']['profile'])

		if 'filter' in url_params['params']:
			query_set = query_set.filter(
				Q(name__icontains = url_params['params']['filter']) | 
				Q(email__icontains = url_params['params']['filter'])
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

@post('/user')
def new():
	try:
		iugu_environment = None
		iugu_token = None
		
		try:
			iugu_environment = Configuration.objects(key='iugu_api_environment').get()
			iugu_environment = iugu_environment.value
		except DoesNotExist as e:
			response.status = 406
			return 'Ambiente de integração c/ IUGU não configurado!'
		
		try:
			iugu_token = Configuration.objects(key='iugu_api_'+ iugu_environment +'_token').get()
			iugu_token = iugu_token.value
		except DoesNotExist as e:
			response.status = 406
			return 'Token de integração c/ IUGU não configurado!'

		api = iugu.config(token=iugu_token)

		# load data from post
		post_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		'''
		try:
			user_exists = User.objects(
				email = post_data['email']
			).filter()

			if not (user_exists is None) and (len(user_exists) > 0):
				response.status = 406
				return 'Já existe um usuário cadastrado com este email!'
		except DoesNotExist as e:
			pass
		'''

		if 'arquivo' in post_data:
			# convert data and create temporary CSV file
			file_path = 'images/'+ str(ObjectId()) +'.'+ post_data['arquivo']['type']
			file = open(file_path, 'wb')
			file.write(base64.decodestring(post_data['arquivo']['path']))
			file.close()

		password = bcrypt.hashpw(post_data['password'].encode('utf-8'), bcrypt.gensalt())

		addressUser = AddressUserData()
		addressUser.street 		= post_data['address']['street']
		addressUser.number 		= post_data['address']['number']
		addressUser.district 	= post_data['address']['district']
		addressUser.city 		= post_data['address']['city']
		addressUser.state 		= post_data['address']['state']
		addressUser.zip_code 	= post_data['address']['zip_code']
		addressUser.complement 	= post_data['address']['complement']

		user = User()
		user.name 			= post_data['name']
		user.email 			= post_data['email']
		user.cpf_cnpj		= post_data['cpf_cnpj']
		user.phone_prefix	= post_data['phone_prefix']
		user.phone 			= post_data['phone']
		user.iugu_id		= post_data['iugu_id']
		user.profile 		= post_data['profile']
		user.photo_path 	= file_path if 'arquivo' in post_data else None
		user.address		= addressUser
		user.password 		= password
		user.save()

		customer_data = {
			'name': 		post_data['name'],
			'email': 		post_data['email'] if 'email' in post_data else None,
			'cpf_cnpj': 	post_data['cpf_cnpj'],
			'zip_code': 	post_data['address']['zip_code'],
			'number':   	post_data['address']['number'],
			'street':   	post_data['address']['street'],
			'city': 		post_data['address']['city'] if 'city' in post_data['address'] else None,
			'state': 		post_data['address']['state'] if 'state' in post_data['address'] else None,
			'district': 	post_data['address']['district'] if 'district' in post_data['address'] else None,
			'complement': 	post_data['address']['complement'] if 'complement' in post_data['address'] else None,
			'custom_variables': [
				{
					'name': 'reference_id',
					'value': str(user.id)
				}
			]
		}

		iugu_customer = iugu.Customer().create(customer_data)

		User.objects(
			id = user.id
		).update_one(
			iugu_id=iugu_customer['id']
		)

		user = User.objects(
			id = user.id
		).get()

		response.status = 201
		response.headers['Content-Type'] = 'application/json'
		return user.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/user/<id:re:[0-9a-f]{24}>')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		user = User.objects(id = id)

		if 'arquivo' in request_data and bool(request_data['arquivo']['changed']) == True:
			if not (user.get().photo_path is None) and os.path.isfile(user.get().photo_path) == True:
				os.remove(user.get().photo_path)

			if 'arquivo' in request_data:
				# convert data and create temporary CSV file
				file_path = 'images/'+ str(ObjectId()) +'.'+ request_data['arquivo']['type']
				file = open(file_path, 'wb')
				file.write(base64.decodestring(request_data['arquivo']['path']))
				file.close()
		else:
			file_path = request_data['photo_path'] if 'photo_path' in request_data else None

		user.update_one(
			name 		= request_data['name'],
			login 		= request_data['login'],
			password 	= bcrypt.hashpw(request_data['password'].encode('utf-8'), bcrypt.gensalt()),
			profile 	= request_data['profile'],
			photo_path 	= file_path
		)

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return user.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@delete('/user/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		User.objects(
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