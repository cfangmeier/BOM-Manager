#!flask/bin/python3
from app import app, context
app.run(debug=True, use_reloader=True, ssl_context=context)
