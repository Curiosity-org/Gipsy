import logging
import datetime
import os
import traceback

from LRFutils import color

__all__ = [
    'GipsyLogs',
    'setup_logger',
]

# Set the filename at start and create logs folder if needed
if not os.path.isdir('logs'):
    os.mkdir('logs')

start = datetime.datetime.now()
default_filename = "logs/{time}.log".format(
    time=start.strftime("%d-%m-%Y_%Hh%Mm%S")
)

# For format reference, see https://strftime.org/
# This format outputs like this : 08/09/2013 at 07:06:05
DATETIME_FORMAT = "%d/%m/%Y at %H:%M:%S"
DATETIME_FORMAT_COLOR = f"{color.fg.blue}%d/%m/%Y{color.stop} at {color.fg.purple}%H:%M:%S{color.stop}"

# Formats and colors depending on the level
LOG_FORMAT = "{date} | [{level}] | {name} | {message}"

LOG_FORMAT_COLOR = "{date} | {color}[{level}]{color_end} | {name} | {message}"
LEVEL_COLORS = {
    logging.DEBUG: color.fg.lightblue,
    logging.INFO: color.fg.green,
    logging.WARNING: color.fg.yellow,
    logging.ERROR: color.fg.red,
    logging.CRITICAL: color.fg.red + color.bold,
}

class GipsyLogs(logging.Formatter):
    """Custom colored logging formatter."""

    def __init__(self, colored: bool = False):
        super().__init__()
        if colored:
            self.log_format = LOG_FORMAT_COLOR
            self.datetime_format = DATETIME_FORMAT_COLOR
        else:
            self.log_format = LOG_FORMAT
            self.datetime_format = DATETIME_FORMAT

    def format(self, record: logging.LogRecord):
        level_color = LEVEL_COLORS.get(record.levelno)
        date = datetime.datetime.fromtimestamp(
            record.created,
        ).strftime(self.datetime_format)

        return self.log_format.format(
            date=date,
            name=record.name,
            color=level_color,
            level=record.levelname,
            color_end=color.stop,
            message=record.getMessage(),
        ) + ('\n'+''.join(traceback.format_exception(*record.exc_info)) if record.exc_info else '')


def setup_logger(
    name: str,
    level=logging.INFO,
    filename: str = default_filename,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Output to the console with color formating
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(GipsyLogs(colored=True))

    logger.addHandler(stdout_handler)

    # Output to a file without colors if needed
    if filename is not None:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(GipsyLogs(colored=False))
    
        logger.addHandler(file_handler)

    return logger

if __name__ == "__main__":
    test_logger = setup_logger(__name__, level=logging.DEBUG, filename="logs/tests.log")

    import random

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message %i", random.randint(0, 10))
    test_logger.warning("This is a warning")
    test_logger.error("Something is wrong, error")
    test_logger.critical("It's the end of the world")
