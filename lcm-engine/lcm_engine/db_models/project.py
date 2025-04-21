from sqlalchemy import (
    Column,
    Integer,
    String,
    LargeBinary,
    Boolean,
    ForeignKey,
)

from lcm_engine.models.project import Project as ApiProject
from lcm_engine.db_models.models import db


class Project(db.Model):
    __tablename__ = "project"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    container_id = Column(String, nullable=False)
    available = Column(Boolean, nullable=False)
    csar = Column(LargeBinary, nullable=False)
    kind = Column(String, nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspace.id"), nullable=False)

    workspace = db.relationship("Workspace", back_populates="projects")

    def to_api_model(self):
        return ApiProject(
            id=self.id,
            name=self.name,
            workspace=self.workspace_id,
            kind=self.kind
        )

    def __repr__(self):
        return f"<Project {self.name}>"
