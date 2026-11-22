from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from PhantomLogic.Database.DatabaseConfig import DatabaseConfig
from PhantomLogic.Database.Models import DatabaseBase


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = DatabaseBase.metadata


def run_migrations_offline() -> None:

    database_url = DatabaseConfig.get_database_url()

    context.configure(
        url=database_url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="work_items",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = create_engine(
        DatabaseConfig.get_database_url(),
        poolclass=NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True,
                compare_type=True,
                version_table_schema="work_items",
            )

            with context.begin_transaction():
                context.run_migrations()

    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()