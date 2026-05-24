import os

from config import get_db_engine

from dashboard.app import create_app

DASH_HOST = os.getenv("DASH_HOST", "127.0.0.1")
DASH_PORT = int(os.getenv("DASH_PORT", "8050"))


def run() -> None:
    engine = get_db_engine()
    app = create_app(engine)
    app.run(host=DASH_HOST, port=DASH_PORT, debug=True)


if __name__ == "__main__":
    run()
