import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec


def global_init(db_base):
    global __factory
    if __factory:
        return
    if not db_base or not db_base.split():
        raise Exception("Необходимо указать файл базы данных.")
    conn_str = f"sqlite:///{db_base.strip()}?check_same_thread=False"
    print("Подключение по " + conn_str)
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


__factory = None
SqlAlchemyBase = dec.declarative_base()
