import ssl
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
from flask_uploads import configure_uploads, UploadSet
from flask_oauthlib.client import OAuth
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config')
sslify = SSLify(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)

uploads = UploadSet('uploads', ('zip'))
configure_uploads(app, (uploads,))

context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.load_cert_chain("ssl/cert.pem", "ssl/key.pem")

oauth = OAuth(app)

from app import views, models
