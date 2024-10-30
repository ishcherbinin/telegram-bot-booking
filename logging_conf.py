
log_config = {
    "version": 1,
    "formatters": {
        "file_formatter": {
            "class": "logging.Formatter",
            "format": "%(processName)s$: %(threadName)s: %(asctime)s - %(levelname)s - %(name)s:"
                      "%(lineno)d - %(message)s"
        },
        "simple_formatter": {
            "class": "logging.Formatter",
            "format": "%(asctime)s - %(levelname)s - %(name)s  - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple_formatter"
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "filename": "bot_logs.log",
            "mode": "w",
            "formatter": "file_formatter",
            "level": "DEBUG"
        }
    },
    "root": {
        "level": "NOTSET",
        "handlers": ["file_handler", "console"],
        "propagate": False
    },
    "disable_existing_loggers": False
}
