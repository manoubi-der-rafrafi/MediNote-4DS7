import os
from urllib.parse import quote_plus


class DatabaseConfigError(RuntimeError):
    pass


def get_database_url() -> str:
    database_url = str(os.environ.get("DATABASE_URL", "")).strip()
    if database_url:
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        return database_url

    host = str(os.environ.get("DB_HOST", "")).strip()
    port = str(os.environ.get("DB_PORT", "3306")).strip() or "3306"
    user = str(os.environ.get("DB_USER", "")).strip()
    password = str(os.environ.get("DB_PASSWORD", "")).strip()
    database_name = str(os.environ.get("DB_NAME", "")).strip()

    missing = [
        key
        for key, value in (
            ("DB_HOST", host),
            ("DB_USER", user),
            ("DB_NAME", database_name),
        )
        if not value
    ]
    if missing:
        raise DatabaseConfigError(
            "Configuration BDD incomplete. Variables manquantes: "
            + ", ".join(missing)
            + ". Renseignez DATABASE_URL ou les variables DB_HOST, DB_PORT, "
            + "DB_USER, DB_PASSWORD, DB_NAME dans flask_api/.env."
        )

    encoded_password = quote_plus(password)
    return (
        f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/{database_name}"
        "?charset=utf8mb4"
    )
