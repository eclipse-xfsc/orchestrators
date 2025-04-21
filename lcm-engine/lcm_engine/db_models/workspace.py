from sqlalchemy import (
    Column,
    Integer,
    String,
)

from lcm_engine.models.workspace import Workspace as ApiWorkspace
from lcm_engine.db_models.models import db


class Workspace(db.Model):
    __tablename__ = "workspace"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    users = db.relationship(
        "UserWorkspace", back_populates="workspace", cascade="all, delete-orphan"
    )
    projects = db.relationship("Project", back_populates="workspace")
    secrets = db.relationship("SecretWorkspace", back_populates="workspace")

    def to_api_model(self, is_owner):
        return ApiWorkspace(
            id=self.id,
            name=self.name,
            projects=[p.id for p in self.projects],
            secrets=[sw.secret.id for sw in self.secrets],
            is_owner=is_owner,
        )

    def __repr__(self):
        return f"<Workspace {self.name}>"
