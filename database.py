import os
from getpass import getuser

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


def build_database_url():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    pg_user = os.getenv("PGUSER", getuser())
    pg_password = os.getenv("PGPASSWORD", "")
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_database = os.getenv("PGDATABASE", "sbc_chatbot")

    if pg_password:
        return (
            f"postgresql+psycopg2://{pg_user}:{pg_password}"
            f"@{pg_host}:{pg_port}/{pg_database}"
        )

    return f"postgresql+psycopg2://{pg_user}@{pg_host}:{pg_port}/{pg_database}"


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database(), current_user;"))
        row = result.fetchone()
        return {
            "database": row[0],
            "user": row[1],
        }


if __name__ == "__main__":
    try:
        result = test_connection()
        print("PostgreSQL connection OK")
        print(f"Database: {result['database']}")
        print(f"User: {result['user']}")
    except Exception as error:
        print("PostgreSQL connection failed")
        print(error)
