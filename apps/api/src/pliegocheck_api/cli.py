"""CLI administrativo de la API."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from uuid import UUID

from sqlalchemy import func, select

from pliegocheck_api.auth import create_user, ensure_roles, user_summary
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import AuthRole, AuthUser, AuthUserRole
from pliegocheck_schemas import AuthRoleName, AuthUserStatus


def _read_password(args: argparse.Namespace) -> str:
    if getattr(args, "password_stdin", False):
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Las contrasenas no coinciden.")
    return password


def _parse_roles(values: list[str]) -> list[AuthRoleName]:
    return [AuthRoleName(value.upper()) for value in values]


def create_admin(args: argparse.Namespace) -> int:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        ensure_roles(session)
        user = create_user(
            session,
            email=args.email,
            display_name=args.display_name,
            password=_read_password(args),
            roles=[AuthRoleName.ADMIN],
        )
        session.commit()
        print(json.dumps({"id": str(user.id), "email": user.email, "roles": ["ADMIN"]}))
    return 0


def bootstrap_admin(args: argparse.Namespace) -> int:
    """Crea el primer ADMIN una sola vez sin reemplazar credenciales existentes."""
    session_factory = get_sessionmaker()
    with session_factory() as session:
        admin_count = session.scalar(
            select(func.count())
            .select_from(AuthUser)
            .join(AuthUserRole)
            .join(AuthRole)
            .where(AuthRole.name == AuthRoleName.ADMIN.value)
        )
        if admin_count:
            print(json.dumps({"status": "already_exists", "admin_count": int(admin_count)}))
            return 0
        ensure_roles(session)
        user = create_user(
            session,
            email=args.email,
            display_name=args.display_name,
            password=_read_password(args),
            roles=[AuthRoleName.ADMIN],
        )
        session.commit()
        print(json.dumps({"status": "created", "id": str(user.id), "roles": ["ADMIN"]}))
    return 0


def create_regular_user(args: argparse.Namespace) -> int:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        user = create_user(
            session,
            email=args.email,
            display_name=args.display_name,
            password=_read_password(args),
            roles=_parse_roles(args.roles),
        )
        session.commit()
        print(json.dumps({"id": str(user.id), "email": user.email, "roles": args.roles}))
    return 0


def list_users(_args: argparse.Namespace) -> int:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        users = session.execute(select(AuthUser).order_by(AuthUser.created_at.desc())).scalars()
        payload = [user_summary(session, user).model_dump(mode="json") for user in users]
        print(json.dumps(payload, sort_keys=True))
    return 0


def disable_user(args: argparse.Namespace) -> int:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        user = session.get(AuthUser, UUID(args.user_id))
        if user is None:
            raise SystemExit("Usuario no encontrado.")
        user.status = AuthUserStatus.DISABLED.value
        session.commit()
        print(json.dumps({"id": str(user.id), "status": user.status}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pliegocheck-api")
    subparsers = parser.add_subparsers(dest="command", required=True)
    users = subparsers.add_parser("users")
    user_commands = users.add_subparsers(dest="user_command", required=True)

    create_admin_parser = user_commands.add_parser("create-admin")
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--display-name", required=True)
    create_admin_parser.add_argument("--password-stdin", action="store_true")
    create_admin_parser.set_defaults(func=create_admin)

    bootstrap_parser = user_commands.add_parser("bootstrap-admin")
    bootstrap_parser.add_argument("--email", required=True)
    bootstrap_parser.add_argument("--display-name", required=True)
    bootstrap_parser.add_argument("--password-stdin", action="store_true", required=True)
    bootstrap_parser.set_defaults(func=bootstrap_admin)

    create_parser = user_commands.add_parser("create")
    create_parser.add_argument("--email", required=True)
    create_parser.add_argument("--display-name", required=True)
    create_parser.add_argument("--role", action="append", dest="roles", default=["VIEWER"])
    create_parser.add_argument("--password-stdin", action="store_true")
    create_parser.set_defaults(func=create_regular_user)

    list_parser = user_commands.add_parser("list")
    list_parser.set_defaults(func=list_users)

    disable_parser = user_commands.add_parser("disable")
    disable_parser.add_argument("user_id")
    disable_parser.set_defaults(func=disable_user)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
