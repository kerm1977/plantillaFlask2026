"""Instancia compartida de Flask-SocketIO usada por app.py y los blueprints."""
from flask_socketio import SocketIO

try:
    import eventlet  # noqa: F401
    ASYNC_MODE = "eventlet"
except Exception:
    ASYNC_MODE = "threading"

socketio = SocketIO(cors_allowed_origins="*", async_mode=ASYNC_MODE)
