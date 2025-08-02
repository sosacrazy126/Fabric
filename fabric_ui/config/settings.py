from dataclasses import dataclass

@dataclass
class Settings:
    APP_NAME: str = "Fabric Studio"

APP_NAME = Settings.APP_NAME