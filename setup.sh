#!/usr/bin/env bash
python -m virtualenv flask
flask/bin/pip install -r requirements.txt
./db_create.py
