import logging.config
import importlib.metadata

import rich.logging

try:
    __version__ = importlib.metadata.version("cloud-provider-mdns")
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = "0.0.0.dev0"

console = rich.console.Console(log_time=True, log_path=False, width=120)

__log_config__ = {
    "version": 1,
    "formatters": {
        "server": {"format": "[%(name)s] %(message)s"},
    },
    "handlers": {
        "server": {
            "()": "rich.logging.RichHandler",
            "show_time": False,
            "show_path": False,
            "formatter": "server",
        },
    },
    "loggers": {
        "": {"level": "INFO", "handlers": ["server"], "propagate": False},
        "cloud_provider_local": {"level": "INFO", "handlers": ["server"], "propagate": False},
    },
}
logging.config.dictConfig(__log_config__)
