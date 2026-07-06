from __future__ import annotations

from pathlib import Path

from seed_platform import create_app
from seed_platform.core.config import Config


class TestConfig(Config):
    TESTING = True
    DATABASE_PATH = Path("test_seed_platform.db")


def test_core_pages_render(tmp_path, monkeypatch):
    database_path = tmp_path / "seed_platform_test.db"
    monkeypatch.setattr(TestConfig, "DATABASE_PATH", database_path)

    app = create_app(TestConfig)
    client = app.test_client()

    for path in ["/", "/farmers", "/seeds", "/distributions", "/reports"]:
        response = client.get(path)
        assert response.status_code == 200
