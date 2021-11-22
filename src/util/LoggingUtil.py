import logging
import os

def init_logger(app):
    logger = logging.getLogger(app.config['LOG_NAME'])
    level_file = logging.getLevelName(app.config['LOG_LEVEL_FILE'])
    level_console = logging.getLevelName(app.config['LOG_LEVEL_CONSOLE'])
    logger.setLevel(level_file)

    # create file handler which logs even debug messages
    if not os.path.exists(os.path.realpath(app.config['LOG_DIR'])):
        os.mkdir(os.path.realpath(app.config['LOG_DIR']))

    fh = logging.FileHandler(os.path.join(
        os.path.realpath(app.config['LOG_DIR']),
        app.config['LOG_NAME']
    ))
    fh.setLevel(level_file)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level_console)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Loaded logger")

    return logger