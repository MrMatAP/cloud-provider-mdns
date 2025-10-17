#  MIT License
#
#  Copyright (c)  2025 Mathieu Imfeld
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

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
        "cloud_provider_local": {
            "level": "INFO",
            "handlers": ["server"],
            "propagate": False,
        },
    },
}
logging.config.dictConfig(__log_config__)
