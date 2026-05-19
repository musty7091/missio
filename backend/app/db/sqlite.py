from sqlalchemy import event
from sqlalchemy.engine import Engine


def configure_sqlite_connection(dbapi_connection, connection_record) -> None:
    """Apply safe SQLite pragmas for each new database connection."""

    del connection_record

    cursor = dbapi_connection.cursor()

    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    cursor.close()


def register_sqlite_pragmas(engine: Engine) -> None:
    """Register SQLite pragma configuration on the given SQLAlchemy engine."""

    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    event.listen(engine, "connect", configure_sqlite_connection)
