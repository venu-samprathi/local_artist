import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# IMPLEMENT DATABASE URL. Include Username and Password
SQLALCHEMY_DATABASE_URI = 'postgres://<username>:<password>@localhost:5432/fyyur'
