from rest_framework_simplejwt.authentication import JWTAuthentication
from wms import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if not self.has_bearer_in_header(header):
            # Fall back to cookie if Bearer header isn't present
            return self.fallback_read_token_from_cookies(request=request)
        return super().authenticate(request)

    def has_bearer_in_header(self, header):
        return header is not None

    def fallback_read_token_from_cookies(self, request):
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'])

        if raw_token is None:
            return None
        
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token