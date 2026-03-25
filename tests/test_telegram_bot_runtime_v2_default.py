from app.telegram_bot import create_bot_from_config
from app.config import load_config


def test_create_bot_from_config_uses_runtime_v2_by_default():
    load_config(validate=False)
    bot = create_bot_from_config()
    assert bot.use_runtime_v2 is True
