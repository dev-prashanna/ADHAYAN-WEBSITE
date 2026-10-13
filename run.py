"""Development entry point.

    python run.py            -> http://127.0.0.1:5000
    gunicorn run:app         -> production
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
    )
