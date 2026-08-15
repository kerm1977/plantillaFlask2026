"""Instancia compartida de Flask-SocketIO usada por app.py y los blueprints."""
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
