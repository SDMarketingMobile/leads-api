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

@get('/vehicle/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return Vehicle.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/vehicles')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = Vehicle.objects(deleted = False).filter()

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

@post('/vehicle')
def new():
	try:
		# load data from post
		post_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		vehicleBrand = VehicleBrandData()
		vehicleBrand.name 				= post_data['brand']['name']
		vehicleBrand.fipe_name 			= post_data['brand']['fipe_name']
		vehicleBrand.order 				= post_data['brand']['order']
		vehicleBrand.key 				= post_data['brand']['key']
		vehicleBrand.id 				= post_data['brand']['id']

		vehicleModel = VehicleModelData()
		vehicleModel.fipe_marca			= post_data['model']['fipe_marca']
		vehicleModel.name				= post_data['model']['name']
		vehicleModel.marca				= post_data['model']['marca']
		vehicleModel.key				= post_data['model']['key']
		vehicleModel.id					= post_data['model']['id']
		vehicleModel.fipe_name			= post_data['model']['fipe_name']

		vehicleVersion = VehicleVersionData()
		vehicleVersion.fipe_marca 		= post_data['version']['fipe_marca']
		vehicleVersion.fipe_codigo 		= post_data['version']['fipe_codigo']
		vehicleVersion.name 			= post_data['version']['name']
		vehicleVersion.marca 			= post_data['version']['marca']
		vehicleVersion.key 				= post_data['version']['key']
		vehicleVersion.veiculo 			= post_data['version']['veiculo']
		vehicleVersion.id 				= post_data['version']['id']

		vehicleInformation = VehicleInformation()
		vehicleInformation.id 			= post_data['information']['id']
		vehicleInformation.ano_modelo 	= post_data['information']['ano_modelo']
		vehicleInformation.marca 		= post_data['information']['marca']
		vehicleInformation.name 		= post_data['information']['name']
		vehicleInformation.veiculo 		= post_data['information']['veiculo']
		vehicleInformation.preco 		= post_data['information']['preco']
		vehicleInformation.combustivel 	= post_data['information']['combustivel']
		vehicleInformation.referencia 	= post_data['information']['referencia']
		vehicleInformation.fipe_codigo 	= post_data['information']['fipe_codigo']
		vehicleInformation.key		 	= post_data['information']['key']

		vehicle = Vehicle()
		vehicle.type 			= post_data['type']
		vehicle.brand 			= vehicleBrand
		vehicle.model 			= vehicleModel
		vehicle.version 		= vehicleVersion
		vehicle.information		= vehicleInformation
		vehicle.plate_number 	= post_data['plate_number']
		vehicle.color_name 		= post_data['color_name']
		vehicle.seats 			= post_data['seats']
		vehicle.save()

		response.status = 201
		response.headers['Content-Type'] = 'application/json'
		return vehicle.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/vehicle/<id:re:[0-9a-f]{24}>')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		vehicleBrand = None
		if ('brand' in request_data) and ('id' in request_data['brand']):
			vehicleBrand = VehicleBrandData()
			vehicleBrand.fipe_name 			= request_data['brand']['fipe_name'] if 'fipe_name' in request_data['brand'] else None
			vehicleBrand.id 				= request_data['brand']['id'] if 'id' in request_data['brand'] else None
			vehicleBrand.key 				= request_data['brand']['key'] if 'key' in request_data['brand'] else None
			vehicleBrand.name 				= request_data['brand']['name'] if 'name' in request_data['brand'] else None
			vehicleBrand.order 				= request_data['brand']['order'] if 'order' in request_data['brand'] else None

		vehicleModel = None
		if ('model' in request_data) and ('id' in request_data['model']):
			vehicleModel = VehicleModelData()
			vehicleModel.fipe_marca			= request_data['model']['fipe_marca'] if 'fipe_marca' in request_data['model'] else None
			vehicleModel.fipe_name			= request_data['model']['fipe_name'] if 'fipe_name' in request_data['model'] else None
			vehicleModel.id					= request_data['model']['id'] if 'id' in request_data['model'] else None
			vehicleModel.key				= request_data['model']['key'] if 'key' in request_data['model'] else None
			vehicleModel.marca				= request_data['model']['marca'] if 'marca' in request_data['model'] else None
			vehicleModel.name				= request_data['model']['name'] if 'name' in request_data['model'] else None

		vehicleVersion = None
		if ('version' in request_data) and ('id' in request_data['version']):
			vehicleVersion = VehicleVersionData()
			vehicleVersion.fipe_codigo 		= request_data['version']['fipe_codigo'] if 'fipe_codigo' in request_data['version'] else None
			vehicleVersion.fipe_marca 		= request_data['version']['fipe_marca'] if 'fipe_marca' in request_data['version'] else None
			vehicleVersion.id 				= request_data['version']['id'] if 'id' in request_data['version'] else None
			vehicleVersion.key 				= request_data['version']['key'] if 'key' in request_data['version'] else None
			vehicleVersion.marca 			= request_data['version']['marca'] if 'marca' in request_data['version'] else None
			vehicleVersion.name 			= request_data['version']['name'] if 'name' in request_data['version'] else None
			vehicleVersion.veiculo 			= request_data['version']['veiculo'] if 'veiculo' in request_data['version'] else None

		vehicleInformation = None
		if ('information' in request_data) and ('id' in request_data['information']):
			vehicleInformation = VehicleInformation()
			vehicleInformation.id = request_data['information']['id'] if 'id' in request_data['information'] else None
			vehicleInformation.ano_modelo = request_data['information']['ano_modelo'] if 'ano_modelo' in request_data['information'] else None
			vehicleInformation.marca = request_data['information']['marca'] if 'marca' in request_data['information'] else None
			vehicleInformation.name = request_data['information']['name'] if 'name' in request_data['information'] else None
			vehicleInformation.veiculo = request_data['information']['veiculo'] if 'veiculo' in request_data['information'] else None
			vehicleInformation.preco = request_data['information']['preco'] if 'preco' in request_data['information'] else None
			vehicleInformation.combustivel = request_data['information']['combustivel'] if 'combustivel' in request_data['information'] else None
			vehicleInformation.referencia = request_data['information']['referencia'] if 'referencia' in request_data['information'] else None
			vehicleInformation.fipe_codigo = request_data['information']['fipe_codigo'] if 'fipe_codigo' in request_data['information'] else None
			vehicleInformation.key = request_data['information']['key'] if 'key' in request_data['information'] else None

		vehicle = Vehicle.objects(id = id)

		vehicle.update_one(
			type 			= request_data['type'] if 'type' in request_data else None,
			brand 			= vehicleBrand,
			model 			= vehicleModel,
			version 		= vehicleVersion,
			information		= vehicleInformation,
			plate_number 	= request_data['plate_number'] if 'plate_number' in request_data else None,
			color_name 		= request_data['color_name']  if 'color_name' in request_data else None,
			seats 			= request_data['seats']  if 'seats' in request_data else None
		)

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return vehicle.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@delete('/vehicle/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		Vehicle.objects(
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