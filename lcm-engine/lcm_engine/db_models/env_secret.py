from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)
from lcm_engine.db_models.models import db


class EnvSecret(db.Model):
    __tablename__ = "env_secret"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)

    secret_id = Column(Integer, ForeignKey("secret.id"), nullable=False)

    secret = db.relationship("Secret", back_populates="env_secrets")

    def to_api_model(self):
        return self.name, self.value

    def __repr__(self):
        return f"<EnvSecret {self.name}>"
