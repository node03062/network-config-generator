import logging

import os
from celery import Celery
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix
from config import STATIC_URL_PATH

# login
#from flask import Flask, flash, redirect, render_template, request, session, abort


# configure logging
debug_mode = os.getenv('DEBUG_MODE', False)
logging_directory = "log"
logFormatter = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


if not os.path.exists(logging_directory):
    os.mkdir(logging_directory)

if debug_mode:
    level = logging.DEBUG
else:
    level = logging.INFO

logging.basicConfig(filename=os.path.join(logging_directory, 'application.log'), level=level, format=logFormatter)

if debug_mode:
    # add console handler when debugging
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(logFormatter))
    logging.getLogger().addHandler(stream_handler)
    logging.getLogger().debug("Start debugging...")

else:
    logging.getLogger().info("Start logging...")

config_class = os.getenv('APP_SETTINGS', "config.DefaultConfig")
logging.getLogger().info("use %s configuration" % config_class)

# configure Flask application
app = Flask(__name__, static_url_path=STATIC_URL_PATH)
app.config.from_object(config_class)
db = SQLAlchemy(app)
# setup the celery client
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

if app.config.get("SECRET_KEY") == "":
    logging.getLogger().error("Secret key not set!")

# verify that the FTP and TFTP directories exist
if not os.path.exists(app.config["TFTP_DIRECTORY"]):
    logging.getLogger().info("create TFTP directory at %s" % app.config["TFTP_DIRECTORY"])
    try:
        os.makedirs(app.config["TFTP_DIRECTORY"])

    except:
        logging.getLogger().error("unable to create TFTP directory on server, TFTP might not work", exc_info=True)

else:
    logging.getLogger().info("set TFTP directory to %s" % app.config["TFTP_DIRECTORY"])

if not os.path.exists(app.config["FTP_DIRECTORY"]):
    logging.getLogger().info("create TFTP directory at %s" % app.config["FTP_DIRECTORY"])
    try:
        os.makedirs(app.config["FTP_DIRECTORY"])
    except:
        logging.getLogger().error("unable to create FTP directory on server, FTP might not work", exc_info=True)

else:
    logging.getLogger().info("set FTP directory to %s" % app.config["FTP_DIRECTORY"])

# required for gunicorn
app.wsgi_app = ProxyFix(app.wsgi_app)

from app import models
from app import views
from app.context_processors import inject_all_project_data
