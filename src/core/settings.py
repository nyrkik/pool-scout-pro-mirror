import yaml
from pathlib import Path
import os

class Settings:
    def __init__(self):
        # Find project root by looking for config directory
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # Go up from src/core to project root
        
        # Try different possible locations for config
        config_paths = [
            project_root / "config" / "settings.yaml",
            Path("config/settings.yaml"),  # Relative from current working directory
            Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        ]
        
        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            raise FileNotFoundError(f"Could not find config/settings.yaml in any of: {config_paths}")
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    @property
    def database_path(self):
        return self.config['database']['path']
    
    @property
    def selenium_host(self):
        return self.config['browser']['selenium_host']
    
    @property
    def flask_port(self):
        return self.config['flask']['port']
    
    @property
    def pdf_download_path(self):
        return self.config['downloads']['directory']

settings = Settings()
