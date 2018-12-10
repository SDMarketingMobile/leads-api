import locale, re, json, hashlib, base64, os, sys, csv, re, jsonpickle, time, datetime
from mongoengine import *
from bottle import request, response
from bson import json_util, ObjectId

'''
' Configurations
'''

VEHICLE_TYPES 	= ('carros','motos','caminhoes')
GENDERS 		= ('male','female')
PAYMENT_METHODS = ('credit_card','bank_slip')
STATUS_OPTIONS 	= ('payment_pending', 'payment_approved', 'payment_refused', 'expired', 'used')

class CustomQuerySet(QuerySet):
	def to_json(self):
		return "[%s]" % (",".join([doc.to_json() for doc in self]))
	def to_json_all(self):
		return "[%s]" % (",".join([doc.to_json_all() for doc in self]))

class CustomBaseDocument(Document):
	# default configurations
	meta = {'queryset_class': CustomQuerySet, 'abstract': True}
	
	# default fields
	created_at 	= DateTimeField(default=datetime.datetime.now)
	deleted 	= BooleanField(default=False)
	deleted_at 	= DateTimeField()
	user_delete = ReferenceField('User')

'''
' EmbeddedDocuments
'''

class AddressUserData(EmbeddedDocument):
	street 		= StringField()
	number 		= StringField()
	district 	= StringField()
	city 		= StringField()
	state 		= StringField()
	zip_code 	= StringField()
	complement 	= StringField()
	id 			= StringField()

class VehicleBrandData(EmbeddedDocument):
	name 		= StringField()
	fipe_name 	= StringField()
	order 		= StringField()
	key 		= StringField()
	id 			= StringField()

class VehicleModelData(EmbeddedDocument):
	fipe_marca 	= StringField()
	name 		= StringField()
	marca 		= StringField()
	key 		= StringField()
	id 			= StringField()
	fipe_name 	= StringField()

class VehicleVersionData(EmbeddedDocument):
	fipe_marca 	= StringField()
	fipe_codigo = StringField()
	name 		= StringField()
	marca 		= StringField()
	key 		= StringField()
	veiculo 	= StringField()
	id 			= StringField()

class VehicleInformation(EmbeddedDocument):
	referencia 	= StringField()
	fipe_codigo = StringField()
	name 		= StringField()
	combustivel = StringField()
	marca 		= StringField()
	ano_modelo 	= StringField()
	preco 		= StringField()
	key 		= StringField()
	time 		= FloatField()
	veiculo 	= StringField()
	id 			= StringField()

class SalePassengerItem(EmbeddedDocument):
	id 				= StringField()
	service			= ReferenceField('Service')
	quantity 		= IntField()
	delivery_time 	= IntField()
	price			= FloatField()
	status			= StringField()
	companies		= ListField(ReferenceField('Person'))
	started_at		= DateTimeField()
	ended_at		= DateTimeField()

'''
' Documents
'''

class Vehicle(CustomBaseDocument):
	meta = {'collection': 'vehicles'}

	type 			= StringField(choices=VEHICLE_TYPES)
	brand 			= EmbeddedDocumentField(VehicleBrandData)
	model 			= EmbeddedDocumentField(VehicleModelData)
	version			= EmbeddedDocumentField(VehicleVersionData)
	information 	= EmbeddedDocumentField(VehicleInformation)
	plate_number 	= StringField()
	color_name 		= StringField()
	seats 			= IntField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		data["created_at"] = data["created_at"].strftime("%d/%m/%Y %H:%M:%S") if "created_at" in data else None
		data["deleted_at"] = data["deleted_at"].strftime("%d/%m/%Y %H:%M:%S") if "deleted_at" in data else None

		return json_util.dumps(data)

class Line(CustomBaseDocument):
	meta = {'collection': 'lines'}

	description  = StringField()
	vehicle 	 = ReferenceField('Vehicle')
	origin 		 = ReferenceField('City')
	destiny 	 = ReferenceField('City')
	person_price = FloatField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		if not (self.vehicle is None):
			data['vehicle'] = self.vehicle.to_mongo()
			data['vehicle']["id"] = str(self.vehicle.id)
			del data['vehicle']['_id']

		if not (self.origin is None):
			data['origin'] = self.origin.to_mongo()
			data['origin']["id"] = str(self.origin.id)
			del data['origin']['_id']

		if not (self.destiny is None):
			data['destiny'] = self.destiny.to_mongo()
			data['destiny']["id"] = str(self.destiny.id)
			del data['destiny']['_id']

		return json_util.dumps(data)

class Route(CustomBaseDocument):
	meta = {'collection': 'routes'}

	line 			= ReferenceField('Line')
	departure_date 	= DateTimeField()
	arrival_date 	= DateTimeField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		data["departure_date"] 	= data["departure_date"].strftime("%d/%m/%Y %H:%M:%S") if "departure_date" in data else None
		data["arrival_date"] 	= data["arrival_date"].strftime("%d/%m/%Y %H:%M:%S") if "arrival_date" in data else None
		data["created_at"] 		= data["created_at"].strftime("%d/%m/%Y %H:%M:%S") if "created_at" in data else None
		data["deleted_at"] 		= data["deleted_at"].strftime("%d/%m/%Y %H:%M:%S") if "deleted_at" in data else None

		if not (self.line is None):
			data['line'] = self.line.to_mongo()
			data['line']["id"] = str(self.line.id)
			del data['line']['_id']

			if not (self.line.origin is None):
				data['line']['origin'] = self.line.origin.to_mongo()
				data['line']['origin']["id"] = str(self.line.origin.id)
				del data['line']['origin']['_id']

			if not (self.line.destiny is None):
				data['line']['destiny'] = self.line.destiny.to_mongo()
				data['line']['destiny']["id"] = str(self.line.destiny.id)
				del data['line']['destiny']['_id']

		return json_util.dumps(data)

class Person(CustomBaseDocument):
	meta = {'collection': 'persons'}

	gender 			= StringField(choices=GENDERS)
	first_name 		= StringField()
	last_name 		= StringField()
	rg 				= StringField()
	cpf				= StringField()
	birth_date		= DateTimeField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		data["birth_date"] = data["birth_date"].strftime("%d/%m/%Y") if "birth_date" in data else None

		return json_util.dumps(data)

class Sale(CustomBaseDocument):
	meta = {'collection': 'sales'}

	customer 		= ReferenceField('User')
	seats 			= ListField(IntField())
	route 			= ReferenceField('Route')
	passengers 		= ListField(ReferenceField('Person'), required=True)
	payment_method 	= StringField(choices=PAYMENT_METHODS)
	status 			= StringField(choices=STATUS_OPTIONS)
	iugu_invoice_id = StringField()
	iugu_invoice_url = StringField()
	iugu_invoice_pdf = StringField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']
		
		data["created_at"] = data["created_at"].strftime("%d/%m/%Y %H:%M:%S") if "created_at" in data else None

		if not (self.customer is None):
			data['customer'] = self.customer.to_mongo()
			data['customer']["id"] = str(self.customer.id)
			del data['customer']['_id']

		if not (self.route is None):
			data['route'] = self.route.to_mongo()
			data['route']["id"] = str(self.route.id)
			del data['route']['_id']

			data['route']["departure_date"] = data['route']["departure_date"].strftime("%d/%m/%y %H:%M") if "departure_date" in data['route'] else None
			data['route']["arrival_date"] = data['route']["arrival_date"].strftime("%d/%m/%y %H:%M") if "arrival_date" in data['route'] else None

			if not (self.route.line is None):
				data['route']['line'] = self.route.line.to_mongo()
				data['route']['line']["id"] = str(self.route.line.id)
				del data['route']['line']['_id']

				if not (self.route.line.origin is None):
					data['route']['line']['origin'] = self.route.line.origin.to_mongo()
					data['route']['line']['origin']["id"] = str(self.route.line.origin.id)
					del data['route']['line']['origin']['_id']

				if not (self.route.line.destiny is None):
					data['route']['line']['destiny'] = self.route.line.destiny.to_mongo()
					data['route']['line']['destiny']["id"] = str(self.route.line.destiny.id)
					del data['route']['line']['destiny']['_id']

		if not (self.passengers is None):
			data['passengers'] = []
			for passenger in self.passengers:
				obj = passenger.to_mongo()
				obj["id"] = str(passenger.id)
				del obj['_id']

				obj["birth_date"] = obj["birth_date"].strftime("%d/%m/%Y") if "birth_date" in obj else None

				data['passengers'].append(obj)

		return json_util.dumps(data)

class User(CustomBaseDocument):
	# Collection configuration
	meta = {'collection': 'users'}

	# Collection fields
	name 			= StringField(required=True)
	email 			= StringField(required=True)
	password 		= DynamicField()
	profile 		= StringField(required=True)
	photo_path 		= StringField()
	cpf_cnpj 		= StringField()
	phone_prefix	= StringField()
	phone			= StringField()
	address			= EmbeddedDocumentField(AddressUserData)
	iugu_id			= StringField()

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		if not (self.password is None):
			del data['password']

		data["created_at"] = data["created_at"].strftime("%d/%m/%Y %H:%M:%S") if "created_at" in data else None
		data["deleted_at"] = data["deleted_at"].strftime("%d/%m/%Y %H:%M:%S") if "deleted_at" in data else None

		return json_util.dumps(data)

class City(CustomBaseDocument):
	# Collection configuration
	meta = {'collection': 'cities'}

	# Collection fields
	name = StringField(required=True)
	federative_unit = StringField(required=True)

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		return json_util.dumps(data)

class Configuration(CustomBaseDocument):
	# Collection configuration
	meta = {'collection': 'configurations'}

	# Collection fields
	key = StringField(required=True)
	value = StringField(required=True)

	def to_json(self):
		data = self.to_mongo()
		data["id"] = str(self.id)
		del data['_id']

		return json_util.dumps(data)