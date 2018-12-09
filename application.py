import bottle, sys
from mongoengine import *
from bottle import get, error, static_file
from controller.business import user, vehicle, person, line, route, sale, city, configuration
from controller.validator.oauth_request_validator import OAuthRequestValidator
from bottle_oauthlib.oauth2 import BottleOAuth2
from oauthlib import oauth2

validator = OAuthRequestValidator()
server = oauth2.Server(validator)

app = application = bottle.default_app()
app.auth = BottleOAuth2(app)
app.auth.initialize(server)

from bottle import hook, route, request, response

_allowed_origin  = '*'
_allowed_methods = 'PUT, GET, POST, DELETE, OPTIONS'
_allowed_headers = 'Authorization, Origin, Accept, Content-Type, X-Requested-With'

connection = connect('leads')

@hook('after_request')
def enable_cors():
	'''Add headers to enable CORS'''
	response.headers['Access-Control-Allow-Origin']  = _allowed_origin
	response.headers['Access-Control-Allow-Methods'] = _allowed_methods
	response.headers['Access-Control-Allow-Headers'] = _allowed_headers

@route('/', method = 'OPTIONS')
@route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return
    
@get('/anexos/<filename>')
def anexos(filename):
    return static_file(filename, root='anexos')

@get('/images/<filename:re:.*\.(jpg|jpeg|png)>')
def images(filename):
    return static_file(filename, root='images')

@error(405)
def not_allowed_handler(error):
	return 'Metod not allowed!'

@app.post('/token')
@app.auth.create_token_response()
def token():
	validator = OAuthRequestValidator()
	try:
		bearer_token = oauth2.BearerToken(request_validator=validator)
		bearer_token.create_token(request=request)
		return bearer_token
	except Exception as e:
		response.status = 500
		return 'Error ocurred: {msg} on {line}'.format(msg=str(e), line=sys.exc_info()[-1].tb_lineno)

if __name__ == '__main__':
	bottle.debug(True)
	bottle.run(reloader=True, host="0.0.0.0")