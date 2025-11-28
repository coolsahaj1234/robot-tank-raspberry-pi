import os

class Settings:
    PROJECT_NAME: str = "Modern Robot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # detect if running on Raspberry Pi (simple check for now)
    IS_RASPBERRY_PI: bool = (os.uname().machine.startswith('arm') or os.uname().machine.startswith('aarch')) if hasattr(os, 'uname') else False
    
    # Force mock mode if not on Pi or explicitly set
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "True").lower() == "true" or not IS_RASPBERRY_PI

settings = Settings()


