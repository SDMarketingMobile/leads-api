# -*- coding: utf-8 -*-
import json, bcrypt, base64, os, sys, jsonpickle, iugu
from . import person
from os import path
from bottle import request, response
from bottle import get, put, post, delete
from bson import ObjectId
from bson import DBRef
from mongoengine import *
from ..model.models import *
from ..util.utils import *

@get('/sale/<id:re:[0-9a-f]{24}>')
def get_by_id(id):
	try:
		response.headers['Content-Type'] = 'application/json'
		return Sale.objects(id=id).get().to_json()
	except DoesNotExist as e:
		response.status = 404
		return 'Nenhum registro encontrado'

@get('/sales')
def get_all():
	try:
		url_params = UrlUtil().url_parse(request.query_string)

		if (not('offset' in url_params)) and (not('limit' in url_params)):
			response.status = 406
			return 'Os parâmetros "offset" e "limit" não foram informados'

		query_set = Sale.objects(deleted = False).filter()

		if 'customer_id' in url_params['params']:
			query_set = query_set.filter(
				customer = DBRef('user', ObjectId(url_params['params']['customer_id']))
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

@post('/sale')
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

		if not('passengers' in post_data):
			response.status = 406
			return 'Nenhum passageiro informado!'

		sale = Sale()
		sale.customer 		= DBRef('users', ObjectId(post_data['customer']['id']))
		sale.seats 			= post_data['seats']
		sale.route			= DBRef('users', ObjectId(post_data['route']['id']))
		sale.payment_method = post_data['payment_method']
		sale.status 		= post_data['status']
		sale.iugu_id 		= post_data['iugu_id']
		
		if 'passengers' in post_data:
			sale.passengers = []
			for item in post_data['passengers']:
				if 'delete' in item and bool(item['delete']) == False:
					obj = person.new(item)
					if not(obj is None):
						sale.passengers.append(DBRef('persons', ObjectId(str(obj.id))))

		sale.save()

		iugu_charge_data = {
			"restrict_payment_method": False,
			"customer_id": post_data['customer']['iugu_id'],
			"email": post_data['customer']['email'],
			"discount_cents": 0,
			"bank_slip_extra_days": 5,
			"keep_dunning": False,
			"items": [{
				"description": post_data['route']['line']['city_origin'] +" ("+ post_data['route']['departure_date'] +") >> "+ post_data['route']['line']['city_destiny'] + " ("+ post_data['route']['arrival_date'] +") : " + str(len(post_data['seats'])) + " Passageiros",
				"quantity": 1 ,#len(post_data['seats']),
				"price_cents": int(((len(post_data['seats']) * post_data['route']['line']['person_price']) * 100))
			}],
			"payer": {
				"cpf_cnpj": post_data['customer']['cpf_cnpj'],
				"name": post_data['customer']['name'],
				"phone_prefix": post_data['customer']['phone_prefix'],
				"phone": post_data['customer']['phone'],
				"email": post_data['customer']['email'],
				"address": {
					"street": post_data['customer']['address']['street'],
					"number": post_data['customer']['address']['number'],
					"district": post_data['customer']['address']['district'],
					"city": post_data['customer']['address']['city'],
					"state": post_data['customer']['address']['state'],
					"zip_code": post_data['customer']['address']['zip_code'],
					"complement": post_data['customer']['address']['complement']
				}
			},
			"order_id": str(sale.id)
		}

		if post_data['payment_method'] == "bank_slip":
			iugu_charge_data['method'] = "bank_slip"
		else:
			iugu_charge_data['method'] = iugu_token
			iugu_charge_data['months'] = 1

		iugu_charge_response = iugu.Token().charge(iugu_charge_data)

		if(('success' in iugu_charge_response) and (bool(iugu_charge_response['success']))):
			Sale.objects(
				id = sale.id
			).update_one(
				iugu_invoice_id = iugu_charge_response['invoice_id'],
				iugu_invoice_url = iugu_charge_response['url'],
				iugu_invoice_pdf = iugu_charge_response['pdf']
			)

			sale = Sale.objects(
				id = sale.id
			).get()

			response.status = 201
			response.headers['Content-Type'] = 'application/json'
			return sale.to_json()
		else:
			Sale.objects(
				id = sale.id
			).delete()

			response.status = 406
			response.headers['Content-Type'] = 'application/json'
			return iugu_charge_response
	except Exception as e:
		if sale.id:
			Sale.objects(
				id = sale.id
			).delete()

		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

@put('/sale/<id:re:[0-9a-f]{24}>/payment-status')
def update(id):
	try:
		request_data = jsonpickle.decode(request.body.read().decode('utf-8'))

		sale = Sale.objects(id = id)

		sale.update_one(
			status = request_data['status']
		)

		response.status = 200
		response.headers['Content-Type'] = 'application/json'
		return sale.to_json()
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)		

@delete('/sale/<id:re:[0-9a-f]{24}>')
def delete(id):
	try:
		Sale.objects(
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