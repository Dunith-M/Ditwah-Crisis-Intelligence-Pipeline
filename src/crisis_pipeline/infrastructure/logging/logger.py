import logging


def get_logger(name: str):
    return logging.getLogger(name)


def log_token_event(record: dict):
    logger = get_logger("token_guard")

    if record["action"] != "allowed":
        logger.warning(
            f'Token issue | action={record["action"]} | tokens={record["tokens"]}'
        )