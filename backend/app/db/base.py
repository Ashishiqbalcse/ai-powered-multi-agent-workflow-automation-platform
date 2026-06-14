from app.db.session import engine
from app.models.audit import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

