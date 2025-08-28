"""
Enterprise Database Configuration
Handles multiple database connections for separated concerns
"""

import sqlite3
from pathlib import Path
from typing import Optional

class DatabaseConfig:
    """Enterprise database configuration with separation of concerns"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Business data database
        self.inspection_db_path = self.data_dir / "inspection_data.db"
        
        # System operational database  
        self.system_db_path = self.data_dir / "system_management.db"
    
    def get_inspection_connection(self) -> sqlite3.Connection:
        """Get connection to inspection business data"""
        conn = sqlite3.connect(self.inspection_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_system_connection(self) -> sqlite3.Connection:
        """Get connection to system management data"""
        conn = sqlite3.connect(self.system_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_connection(self, db_type: str) -> sqlite3.Connection:
        """Get connection by database type"""
        if db_type == "inspection":
            return self.get_inspection_connection()
        elif db_type == "system":
            return self.get_system_connection()
        else:
            raise ValueError(f"Unknown database type: {db_type}")

# Global instance
db_config = DatabaseConfig()
