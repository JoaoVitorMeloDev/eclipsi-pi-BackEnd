from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from api.core.database import get_db


bp = Blueprint("auth_v1", __name__, url_prefix="/api/v1/auth")


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET não configurado.")
    return secret


def _issue_token(user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=12),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def _public_user(row) -> dict:
    return {
        "id": str(row[0]),
        "nome": row[1],
        "email": row[2],
        "telefone": row[3],
        "role": row[4],
    }


@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("senha") or data.get("password") or "")
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Informe email e senha.",
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "select id, nome, email, telefone, role, senha "
            "from public.users where lower(email) = %s",
            (email,),
        )
        row = cur.fetchone()
        if not row or not check_password_hash(row[5], password):
            return jsonify({
                "success": False,
                "message": "Email ou senha inválidos.",
            }), 401

        user = _public_user(row)
        token = _issue_token(int(row[0]), row[2], row[4])
        return jsonify({
            "success": True,
            "token": token,
            "access_token": token,
            "user": user,
        }), 200
    except RuntimeError as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    except Exception:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": "Não foi possível realizar o login.",
        }), 500
    finally:
        conn.close()


def _register(role: str):
    data = request.get_json() or {}
    required = ("nome", "email", "senha")
    if any(not str(data.get(field) or "").strip() for field in required):
        return jsonify({
            "success": False,
            "message": "Nome, email e senha são obrigatórios.",
        }), 400

    nome = str(data["nome"]).strip()
    email = str(data["email"]).strip().lower()
    password = str(data["senha"])
    telefone = "".join(ch for ch in str(data.get("telefone") or "") if ch.isdigit())
    if telefone and len(telefone) not in (10, 11):
        return jsonify({
            "success": False,
            "message": "Telefone deve conter 10 ou 11 dígitos.",
        }), 400
    telefone = telefone or None
    idade = data.get("idade")
    genero = data.get("genero")
    especialidade = data.get("especialidade")
    registro = data.get("registro")
    uf = data.get("uf")
    descricao = data.get("descricao")
    valor_hora = data.get("valor_hora")

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "select id from public.users where lower(email) = %s",
            (email,),
        )
        if cur.fetchone():
            return jsonify({
                "success": False,
                "message": "Este email já está cadastrado.",
            }), 409

        cur.execute(
            """insert into public.users
               (nome, email, senha, telefone, role, idade, genero,
                especialidade, registro, uf, descricao, valor_hora)
               values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               returning id, nome, email, telefone, role""",
            (
                nome,
                email,
                generate_password_hash(password),
                telefone,
                role,
                idade,
                genero,
                especialidade,
                registro,
                uf,
                descricao,
                valor_hora,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        user = _public_user(row)
        token = _issue_token(int(row[0]), row[2], row[4])
        return jsonify({
            "success": True,
            "token": token,
            "access_token": token,
            "user": user,
        }), 201
    except RuntimeError as exc:
        conn.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    except Exception:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": "Não foi possível realizar o cadastro.",
        }), 500
    finally:
        conn.close()


@bp.post("/register/user")
def register_user():
    return _register("paciente")


@bp.post("/register/doctor")
def register_doctor():
    return _register("medico")
