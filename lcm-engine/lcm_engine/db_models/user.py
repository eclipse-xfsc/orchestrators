from sqlalchemy import (
    Column,
    Integer,
    String,
)
from lcm_engine.db_models.models import db


class User(db.Model):
    __tablename__ = "user"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    oidc_identifier = Column(String, unique=True, nullable=False)

    secrets = db.relationship("Secret", back_populates="user")
    workspaces = db.relationship("UserWorkspace", back_populates="user")

    def __repr__(self):
        return f"<User {self.oidc_identifier}>"
