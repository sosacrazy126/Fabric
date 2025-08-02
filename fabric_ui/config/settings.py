from dataclasses import dataclass

@dataclass
class AppConfig:
    APP_NAME: str = "Fabric Studio"
    VERSION: str = "0.1.0"

APP_NAME = AppConfig.APP_NAME