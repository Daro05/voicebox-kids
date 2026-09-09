import logging

from voicebox.main import configure_logging


def test_http_request_logs_are_silenced_to_protect_bot_token() -> None:
    http_logger = logging.getLogger("httpx")
    original_level = http_logger.level
    try:
        http_logger.setLevel(logging.INFO)

        configure_logging()

        assert http_logger.level == logging.WARNING
    finally:
        http_logger.setLevel(original_level)
