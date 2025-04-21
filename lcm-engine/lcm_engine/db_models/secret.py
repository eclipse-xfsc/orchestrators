from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)

from lcm_engine.models.secret import Secret as ApiSecret
from lcm_engine.db_models.models import db


class Secret(db.Model):
    __tablename__ = "secret"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="secrets")
    workspaces = db.relationship("SecretWorkspace", back_populates="secret")

    file_secrets = db.relationship("FileSecret", back_populates="secret")
    env_secrets = db.relationship("EnvSecret", back_populates="secret")

    def to_api_model(self, disclose_contents=False):
        kwargs = dict(
            id=self.id,
            name=self.name,
            workspaces=[sw.workspace.id for sw in self.workspaces],
        )
        if self.file_secrets:
            for file_secret in self.file_secrets:
                fs = file_secret.to_api_model(disclose_contents=disclose_contents)
                kwargs["file"] = fs
        if self.env_secrets:
            kwargs["env"] = dict(env.to_api_model() for env in self.env_secrets)

        return ApiSecret(**kwargs)

    def __repr__(self):
        return f"<Secret {self.name}>"
