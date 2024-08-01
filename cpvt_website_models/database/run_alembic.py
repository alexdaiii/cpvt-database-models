import os

from alembic import command
from alembic.config import Config

from app.settings import get_settings
from app.util import get_location


def reset_with_alembic():
    downgrade_to_base()
    upgrade_to_head()


def downgrade_to_base():
    # Create a Config object that represents the Alembic configuration
    alembic_cfg = Config(os.path.join(get_location(), "alembic_v1.ini"))

    alembic_cfg.set_main_option(
        "script_location", os.path.join(get_location(), "../../alembic")
    )

    # Get the base revision from the settings
    base_revision = get_settings().alembic_base_revision

    # Run the Alembic downgrade command to the base revision
    command.downgrade(alembic_cfg, base_revision)


def upgrade_to_head():
    # Create a Config object that represents the Alembic configuration
    alembic_cfg = Config(os.path.join(get_location(), "alembic_v1.ini"))

    alembic_cfg.set_main_option(
        "script_location", os.path.join(get_location(), "../../alembic")
    )

    # Run the Alembic upgrade command to the last V1 version
    command.upgrade(alembic_cfg, "734e7cc14399")


if __name__ == "__main__":
    reset_with_alembic()


__all__ = [
    "reset_with_alembic",
]
