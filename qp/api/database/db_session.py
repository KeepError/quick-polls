import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(db_file):
    """Database init"""
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("No database file specified.")

    conn_str = f"sqlite:///{db_file.strip()}?check_same_thread=False"
    print(f"Connecting to the database at {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
