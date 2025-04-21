from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

db.metadata.schema = "public"
