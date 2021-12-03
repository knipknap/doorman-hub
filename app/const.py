import os

__dirname__ = os.path.dirname(__file__)
crypto_salt = os.environ['CRYPTO_SALT']

google_api_key = os.environ['GOOGLE_API_KEY']

support_email = os.environ['SUPPORT_EMAIL']
smtp_server = os.environ['SMTP_SERVER_AND_PORT']
smtp_user = os.environ['SMTP_USER']
smtp_from = support_email
smtp_password = os.environ['SMTP_PASSWORD']

session_timeout = 7776000
db_file = os.path.join(__dirname__, 'hub.db')
static_dir = os.path.join(__dirname__, 'static')
