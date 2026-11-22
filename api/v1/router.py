"""Registro centralizado dos endpoints públicos da API."""

from __future__ import annotations

from flask import Flask

from .endpoints.admin import bp as admin_bp
from .endpoints.auth import bp as auth_bp
from .endpoints.chat import bp as chat_bp
from .endpoints.doctor import bp as doctor_bp
from .endpoints.patient import bp as patient_bp
from .endpoints.payments import bp as payments_bp
from .endpoints.quiz import bp as quiz_bp
from .endpoints.reviews import bp as reviews_bp


API_BLUEPRINTS = (
    auth_bp,
    patient_bp,
    admin_bp,
    doctor_bp,
    payments_bp,
    chat_bp,
    quiz_bp,
    reviews_bp,
)


def register_api_routes(app: Flask) -> None:
    """Registra todas as rotas versionadas sem alterar as URLs existentes."""
    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)
