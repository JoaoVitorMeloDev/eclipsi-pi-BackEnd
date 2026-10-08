"""Ponto de entrada da API Flask EcliPsi."""

from __future__ import annotations

import os

from flask import Flask, g, jsonify
from flask_cors import CORS

from api.core.config import cors_origins
from api.core.security import require_auth
from api.v1.router import register_api_routes


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": cors_origins()}})

    register_api_routes(app)

    @app.get("/health")
    def health():
        return jsonify({"success": True, "service": "eclipsi-api"})

    @app.get("/api/me")
    @require_auth
    def current_user():
        return jsonify(
            {
                "success": True,
                "user": {
                    "id": getattr(g, "auth_user_id", None),
                    "email": getattr(g, "auth_user", {}).get("email"),
                    "role": getattr(g, "auth_user", {}).get("role", "authenticated"),
                },
            }
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
