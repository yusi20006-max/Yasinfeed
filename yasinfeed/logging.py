import logging
import os
import sys

def setup_logging(config: dict) -> logging.Logger:
    """
    Sets up the logging foundation for YasinFeed.
    Configures console logging and optional file logging according to the config dict.
    Returns the configured root logger.
    """
    log_config = config.get("logging", {})
    level_name = log_config.get("level", "INFO").upper()
    file_path = log_config.get("file_path", "yasinfeed.log")
    console_enabled = log_config.get("console", True)

    # Map log level names to logging constants
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = levels.get(level_name, logging.INFO)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicates
    if logger.handlers:
        for handler in list(logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
            logger.removeHandler(handler)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # File Handler
    if file_path:
        try:
            # Ensure parent directory exists for log file
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            # Print failure to stderr so it is visible but does not crash startup
            print(f"Warning: Failed to setup file log handler at {file_path}: {e}", file=sys.stderr)

    # Specific logger for YasinFeed to avoid log pollution
    yasinfeed_logger = logging.getLogger("yasinfeed")
    yasinfeed_logger.setLevel(level)

    yasinfeed_logger.info("Logging initialized with level: %s", level_name)
    if file_path:
        yasinfeed_logger.info("File logger enabled. Path: %s", file_path)

    return yasinfeed_logger
