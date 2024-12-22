import logging.config
import importlib.metadata

import rich.console

try:
    __version__ = importlib.metadata.version("kube-mdns")
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = "0.0.0.dev0"

console = rich.console.Console(log_time=False, log_path=False)

