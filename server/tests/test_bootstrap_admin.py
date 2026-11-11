from types import SimpleNamespace
import logging

import pytest
from fastapi.testclient import TestClient

import main as api_main
from app import bootstrap_admin
from app.config.settings import Settings
from app.services.auth_service import AuthService
from app.utils.security import hash_password


class FakeSession:
    def __init__(self, existing_user=None):
        self.existing_user = existing_user
        self.added_user = None
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def scalar(self, _query):
        return self.existing_user or self.added_user

    def add(self, user):
        self.added_user = user

    def flush(self):
        pass

    def commit(self):
        self.commit_count += 1

    def refresh(self, _user):
        pass

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


@pytest.fixture
def configured_bootstrap(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(bootstrap_admin, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        bootstrap_admin.settings,
        "admin_email",
        "admin.teste@ecocontrol.com",
    )
    monkeypatch.setattr(
        bootstrap_admin.settings,
        "admin_password",
        "SenhaTeste123!",
    )
    monkeypatch.setattr(
        bootstrap_admin.settings,
        "admin_name",
        "Administrador Teste",
    )
    return session


def test_bootstrap_creates_active_admin_and_login_accepts_password(
    configured_bootstrap,
    caplog,
):
    session = configured_bootstrap
    caplog.set_level(logging.INFO, logger="app.bootstrap_admin")

    bootstrap_admin.bootstrap_initial_admin()

    admin = session.added_user
    assert admin.email == "admin.teste@ecocontrol.com"
    assert admin.full_name == "Administrador Teste"
    assert admin.role == "admin"
    assert admin.active is True
    assert admin.hashed_password != "SenhaTeste123!"

    authenticated_user, token = AuthService(session).login(
        "admin.teste@ecocontrol.com",
        "SenhaTeste123!",
    )
    assert authenticated_user is admin
    assert token
    assert session.commit_count == 1
    assert session.closed is True
    assert "Initial administrator created: admin.teste@ecocontrol.com" in caplog.text
    assert "SenhaTeste123!" not in caplog.text


def test_bootstrap_does_not_change_existing_user(configured_bootstrap, caplog):
    session = configured_bootstrap
    caplog.set_level(logging.INFO, logger="app.bootstrap_admin")
    existing_user = SimpleNamespace(
        email="admin.teste@ecocontrol.com",
        hashed_password=hash_password("ExistingPassword123!"),
        role="analyst",
        active=False,
    )
    session.existing_user = existing_user

    bootstrap_admin.bootstrap_initial_admin()

    assert session.added_user is None
    assert existing_user.role == "analyst"
    assert existing_user.active is False
    assert session.commit_count == 0
    assert session.closed is True
    assert (
        "Initial administrator already exists: admin.teste@ecocontrol.com"
        in caplog.text
    )


@pytest.mark.parametrize(
    ("admin_email", "admin_password"),
    [
        ("", "SenhaTeste123!"),
        ("admin.teste@ecocontrol.com", ""),
    ],
)
def test_bootstrap_skips_when_email_or_password_is_empty(
    monkeypatch,
    admin_email,
    admin_password,
):
    def fail_if_session_is_created():
        pytest.fail("Database session must not be opened")

    monkeypatch.setattr(
        bootstrap_admin,
        "SessionLocal",
        fail_if_session_is_created,
    )
    monkeypatch.setattr(
        bootstrap_admin.settings,
        "admin_email",
        admin_email,
    )
    monkeypatch.setattr(
        bootstrap_admin.settings,
        "admin_password",
        admin_password,
    )

    bootstrap_admin.bootstrap_initial_admin()


def test_admin_settings_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin.teste@ecocontrol.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "SenhaTeste123!")
    monkeypatch.setenv("ADMIN_NAME", "Administrador Teste")

    settings = Settings(_env_file=None)

    assert settings.admin_email == "admin.teste@ecocontrol.com"
    assert settings.admin_password == "SenhaTeste123!"
    assert settings.admin_name == "Administrador Teste"


def test_bootstrap_rolls_back_and_closes_session_on_error(
    configured_bootstrap,
    monkeypatch,
):
    session = configured_bootstrap

    class FailingUserService:
        def __init__(self, _db):
            pass

        def create_user(self, _payload):
            raise RuntimeError("creation failed")

    monkeypatch.setattr(
        bootstrap_admin,
        "UserService",
        FailingUserService,
    )

    with pytest.raises(RuntimeError, match="creation failed"):
        bootstrap_admin.bootstrap_initial_admin()

    assert session.rollback_count == 1
    assert session.closed is True


def test_fastapi_startup_runs_admin_bootstrap(monkeypatch):
    startup_calls = []
    monkeypatch.setattr(
        api_main,
        "bootstrap_initial_admin",
        lambda: startup_calls.append(True),
    )

    with TestClient(api_main.app):
        assert startup_calls == [True]
