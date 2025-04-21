from pathlib import Path
from sqlalchemy import (
    Column,
    Integer,
    String,
    LargeBinary,
    ForeignKey,
)
from lcm_engine.db_models.models import db
from lcm_engine.models.secret_file import SecretFile


class FileSecret(db.Model):
    __tablename__ = "file_secret"
    __table_args__ = dict(schema="public")

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, nullable=False)
    contents = Column(LargeBinary, nullable=False)
    # TODO: figure out how to enable extensions (i.e., pgcrypto) for a
    # non-super user in postgresql and then use the following computed column
    # contents_hash = Column(
    #     String,
    #     Computed("encode(digest(contents, 'sha512'), 'hex')"),
    #     nullable=False,
    # )
    contents_hash = Column(String, nullable=False)

    secret_id = Column(Integer, ForeignKey("secret.id"), nullable=False)

    secret = db.relationship("Secret", back_populates="file_secrets")

    def to_api_model(self, disclose_contents=False):
        kwargs = dict(path=self.path)
        if disclose_contents:
            kwargs["contents"] = self.contents.decode()
        else:
            kwargs["contents_hash"] = self.contents_hash

        return SecretFile(**kwargs)

    def __repr__(self):
        return f"<FileSecret {self.path}>"
