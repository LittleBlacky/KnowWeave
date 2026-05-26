from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import model registry modules so Alembic sees future table metadata.
from app import models as models  # noqa: E402,F401
