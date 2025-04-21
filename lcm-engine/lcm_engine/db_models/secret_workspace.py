from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
)
from lcm_engine.db_models.models import db


class SecretWorkspace(db.Model):
    __tablename__ = "secret_workspace"
    __table_args__ = dict(schema="public")

    secret_id = Column(
        Integer, ForeignKey("secret.id"), nullable=False, primary_key=True
    )
    workspace_id = Column(
        Integer, ForeignKey("workspace.id"), nullable=False, primary_key=True
    )

    secret = db.relationship("Secret", back_populates="workspaces")
    workspace = db.relationship("Workspace", back_populates="secrets")

    def to_api_model(self):
        return dict(secret_id=self.secret_id, workspace_id=self.workspace_id)

    def __repr__(self):
        return f"<SecretWorkspace {self.secret_id}-{self.workspace_id}>"
