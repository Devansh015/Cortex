"""
Configuration and initialization for the ingestion pipeline.
"""

import os
from typing import Dict, Any


class IngestionConfig:
    """Configuration settings for the ingestion pipeline"""
    
    # Text Processing
    MIN_TEXT_LENGTH: int = 5
    MAX_TEXT_LENGTH: int = 100_000
    
    # Chunking
    DEFAULT_CHUNKING_STRATEGY: str = "semantic"
    SEMANTIC_CHUNK_SIZE: int = 512
    SEMANTIC_CHUNK_OVERLAP: int = 128
    MIN_CHUNK_SIZE: int = 100
    
    # GitHub Processing
    GITHUB_API_TIMEOUT: int = 10
    GITHUB_MAX_README_LENGTH: int = 10_000
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # PDF Processing
    PDF_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    PDF_MAX_PAGES: int = 500
    PDF_TIMEOUT: int = 30
    
    # Backboard.io
    BACKBOARD_API_KEY: str = os.getenv("BACKBOARD_API_KEY", "")
    BACKBOARD_API_URL: str = "https://app.backboard.io/api"
    BACKBOARD_ASSISTANT_ID: str = os.getenv("BACKBOARD_ASSISTANT_ID", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Get all config as dictionary"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and key.isupper()
        }
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        issues = []
        
        # Check Backboard config (optional for development)
        if not cls.BACKBOARD_API_KEY and os.getenv("ENV") == "production":
            issues.append("BACKBOARD_API_KEY not set in production")
        
        # Check text length constraints
        if cls.MIN_TEXT_LENGTH < 1:
            issues.append("MIN_TEXT_LENGTH must be positive")
        
        if cls.MAX_TEXT_LENGTH <= cls.MIN_TEXT_LENGTH:
            issues.append("MAX_TEXT_LENGTH must be greater than MIN_TEXT_LENGTH")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
        }


# Test configuration
if __name__ == "__main__":
    config = IngestionConfig()
    print("Configuration:")
    for key, value in config.to_dict().items():
        # Mask sensitive keys
        if "KEY" in key or "TOKEN" in key:
            value = "***" if value else "(not set)"
        print(f"  {key}: {value}")
    
    print("\nValidation:")
    validation = config.validate()
    print(f"  Valid: {validation['is_valid']}")
    if validation['issues']:
        for issue in validation['issues']:
            print(f"  ⚠ {issue}")
