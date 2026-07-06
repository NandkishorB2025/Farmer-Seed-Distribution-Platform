from __future__ import annotations

from flask import Flask

from app.core.config import Config
from app.core import database
from app.modules.seed_portal.routes import seed_portal_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(config_object.TEMPLATES_DIR),
        static_folder=str(config_object.STATIC_DIR),
    )
    app.config.from_object(config_object)

    database.init_app(app)
    app.register_blueprint(seed_portal_bp)

    return app
