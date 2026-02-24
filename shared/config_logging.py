import logging
import sys


def setup_logging(level=logging.INFO):
    """Configura o logging para todo o projeto"""

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("mysql").setLevel(logging.WARNING)
