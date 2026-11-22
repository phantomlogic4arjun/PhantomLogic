
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from PhantomLogic.Database.DatabaseConfig import DatabaseConfig


class DatabaseManager:

    _engine: Engine | None = None
    _session_factory: sessionmaker[Session] | None = None

    @classmethod
    def get_engine(cls) -> Engine:

        if cls._engine is None:
            cls._engine = create_engine(
                DatabaseConfig.get_database_url(),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
            )

        return cls._engine

    @classmethod
    def get_session_factory(cls) -> sessionmaker[Session]:

        if cls._session_factory is None:
            cls._session_factory = sessionmaker(
                bind=cls.get_engine(),
                expire_on_commit=False,
            )

        return cls._session_factory

    @classmethod
    def get_session(cls) -> Session:

        return cls.get_session_factory()()

    @classmethod
    def dispose_engine(cls) -> None:

        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
