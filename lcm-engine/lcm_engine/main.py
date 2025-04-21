#!/usr/bin/env python3
import os
import logging

import connexion
from flask.logging import default_handler

from lcm_engine import encoder
from lcm_engine.db_models.models import db


def init_db(flask_app):
    con_str = os.getenv("LCM_ENGINE_DB_CONNECTION_STRING")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = con_str
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    flask_app.app_context().push()

    db.app = flask_app
    db.init_app(flask_app)

    db.create_all()


def create_app(specification_dir="./openapi"):
    app = connexion.App(__name__, specification_dir=specification_dir)
    return app


def get_config(flask_app):
    hostname = os.getenv("LCM_ENGINE_HOSTNAME")
    flask_app.config["LCM_ENGINE_HOSTNAME"] = hostname

    cert_name = os.getenv("LCM_ENGINE_CERTIFICATE_SECRET_NAME")
    flask_app.config["LCM_ENGINE_CERTIFICATE_SECRET_NAME"] = cert_name


def main():
    con_app = create_app()

    root_logger = logging.getLogger()
    root_logger.addHandler(default_handler)
    flask_debug = os.getenv("FLASK_DEBUG", False)
    if flask_debug is not None:
        flask_debug = flask_debug.lower() in ("1", "true", "yes", "t")
    root_logger.setLevel(logging.DEBUG if flask_debug else logging.INFO)

    con_app.app.json_encoder = encoder.JSONEncoder
    con_app.add_api(
        "openapi.yaml",
        arguments=dict(title="LCM Engine API"),
        strict_validation=True,
        validate_responses=True,
        pythonic_params=True,
    )

    get_config(con_app.app)
    init_db(con_app.app)

    con_app.run(port=8080, server="gevent")


if __name__ == "__main__":
    main()
