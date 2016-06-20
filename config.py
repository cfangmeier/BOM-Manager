import os
basedir = os.path.abspath(os.path.dirname(__file__))

LOG_LEVEL = 'INFO'

# **********************************************************************************
# *  DIGIKEY OAUTH 2
# **********************************************************************************
# This information is obtained upon registration of a new Digikey OAuth
# application here: https://api-portal.digikey.com/
DIGIKEY_CONSUMER_KEY = 'a78ba99c-960f-4267-83de-bf4dd5f67f28'
DIGIKEY_CONSUMER_SECRET = 'gM8eG5pN1lG0eO6yV1tG5vM4nX8xH4cI6xG3xJ6fC8mO3fT3mI'
DIGIKEY_AUTHORIZE_URL = 'https://sso.digikey.com/as/authorization.oauth2'
DIGIKEY_ACCESS_TOKEN_URL = 'https://sso.digikey.com/as/token.oauth2'
DIGIKEY_BASE_URL = 'https://api.digikey.com/services/basicsearch/v1/'

# **********************************************************************************
# * SQL CONFIGURATION
# **********************************************************************************
SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

###############################################################################
# WTF CONFIGURATION
###############################################################################
WTF_CSRF_ENABLED = True
SECRET_KEY = 'hJeqWmafXUxEQ3RRSFMkMDyg7'

###############################################################################
# FLASK UPLOADS CONFIGURATION
###############################################################################
UPLOADED_UPLOADS_DEST = os.path.join(basedir, 'uploads')


SQLALCHEMY_TRACK_MODIFICATIONS = True
