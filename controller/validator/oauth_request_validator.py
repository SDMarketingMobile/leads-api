from ..model.models import User
from oauthlib.oauth2 import RequestValidator

class OAuthRequestValidator(RequestValidator):

	def validate_client_key(self, client_key, request):
		try:
			User.objects(id=client_key).get()
			return True
		except DoesNotExist as e:
			return False