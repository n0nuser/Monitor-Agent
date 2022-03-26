import logging


def getLogger(CONFIG):
    log_level = ""
    tranlation = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    try:
        if CONFIG.logging.level in tranlation.keys():
            log_level = tranlation[CONFIG.logging.level]
        else:
            logging.warning("Level not established in Settings.json")
            log_level = logging.info
    except AttributeError as e:
        logging.warning(
            "Level not established in Settings.json.\nDefault Info level will be used.",
            exc_info=True,
        )
        log_level = logging.info

    log_filename = ""
    try:
        log_filename = CONFIG.logging.filename
    except AttributeError as e:
        logging.warning(
            'Log filename not established in Settings.json.\nDefault "monitor.log" file will be used.',
            exc_info=True,
        )
        log_filename = "monitor.log"

    return logging.basicConfig(
        level=log_level,
        filename=log_filename,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
