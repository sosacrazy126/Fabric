import logging

def setup_logging():
    """Set up basic logging format."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
        level=logging.INFO
    )