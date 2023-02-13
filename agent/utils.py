import logging
from logging.handlers import SysLogHandler


def create_logger(
    name,
    level="info",
    service="",
    fmt=None,
    datefmt="%Y-%m-%d %H:%M:%S",
    add_console_handler=True,
    add_sys_handler=False,
):
    """Create a formatted logger
    Args:
        name: name of the logger, typically the name of the script
        service: service name
        level: logging level
        fmt: Format of the log message
        datefmt: Datetime format of the log message
        add_console_handler: whether to add a console handler
        add_sys_handler: whether to add a sys handler
    Examples:
        logger = create_logger(__name__, level="info")
        logger.info("Hello world")
    """

    level = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }.get(level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not fmt:
        if service:
            fmt = f"%(asctime)s {service} %(levelname)s %(name)s: %(message)s"
        else:
            fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    if add_console_handler:  # Output to stdout
        ch = logging.StreamHandler()
        ch.setLevel(level)
        chformatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        ch.setFormatter(chformatter)
        logger.addHandler(ch)

    if add_sys_handler:  # Output to syslog
        sh = SysLogHandler(address="/dev/log")
        sh.setLevel(level)
        formatter = logging.Formatter(
            fmt='Python: { "loggerName":"%(name)s", "timestamp":"%(asctime)s", "pathName":"%(pathname)s", '
            '"logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s"'
            ', "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}',
            datefmt=datefmt,
        )
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger
