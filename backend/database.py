import os

# Bestimme das absolute Hauptverzeichnis des Projekts (eine Ebene über backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")

DATABASE_CONFIG = {
    "connections": {
        "default": f"sqlite://{DB_PATH}"
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        }
    }
}
