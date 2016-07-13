#!flask/bin/python3
import webbrowser
from app import app, context
webbrowser.open_new_tab("https://localhost:8080/")
app.run(port=8080,
        debug=True,
        use_reloader=True,
        ssl_context=context)
