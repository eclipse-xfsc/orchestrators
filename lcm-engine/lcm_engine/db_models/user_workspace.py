from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    ForeignKey,
)
from lcm_engine.db_models.models import db


class UserWorkspace(db.Model):
    __tablename__ = "user_workspace"
    __table_args__ = dict(schema="public")

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, primary_key=True)
    workspace_id = Column(
        Integer, ForeignKey("workspace.id"), nullable=False, primary_key=True
    )
    is_owner = Column(Boolean, nullable=False)

    user = db.relationship("User", back_populates="workspaces")
    workspace = db.relationship("Workspace", back_populates="users")

    def to_api_model(self):
        return dict(
            user_id=self.user_id, workspace_id=self.workspace_id, is_owner=self.is_owner
        )

    def __repr__(self):
        return "<UserWorkspace " f"{self.user_id}-{self.workspace_id}>"
