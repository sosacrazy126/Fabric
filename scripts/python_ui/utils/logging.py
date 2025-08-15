import logging, os
from datetime import datetime

logger = logging.getLogger("fabric_ui")

def init() -> None:
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

    log_dir = os.path.expanduser("~/.config/fabric/logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, f"fabric_ui_{datetime.now():%Y%m%d}.log"))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(fh)

    logger.info("Fabric UI logging initialized")