import os
from app import app
from shiny import run_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    # listen on all interfaces so container port mapping works
    run_app(app, host="0.0.0.0", port=port)
