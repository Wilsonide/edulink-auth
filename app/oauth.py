from authlib.integrations.starlette_client import OAuth,OAuthError
from settings import setting

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id= setting.GOOGLE_CLIENT_ID,
    client_secret= setting.GOOGLE_CLIENT_SECRET,
    client_kwargs= {
        "scope": "email openid profile",
        "redirect_url": "http://localhost:8000/auth/google-auth"
    }
)