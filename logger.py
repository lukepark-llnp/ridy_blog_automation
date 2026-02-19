"""Structured logging for blog publishing"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class PublishLogger:
    """Log publish attempts with structured data"""
    
    def __init__(self, output_dir: str = "./logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_data = {}
        self.log_file = None
    
    def start(self, user_id: str, data: dict):
        """Start logging a publish attempt"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.output_dir / f"{timestamp}_{user_id}.json"
        
        self.log_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "status": "in_progress",
            "input_data": data,
            "steps": {},
            "errors": [],
            "result": {}
        }
        
        self._save()
        logger.info(f"Started logging: {self.log_file}")
    
    def log_step(self, step: str, status: str, details: dict = None):
        """Log a processing step"""
        self.log_data["steps"][step] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self._save()
    
    def log_error(self, step: str, error: Exception):
        """Log an error"""
        error_data = {
            "step": step,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.log_data["errors"].append(error_data)
        self.log_data["status"] = "error"
        self._save()
        logger.error(f"Logged error in {step}: {error}")
    
    def finish(self, success: bool, result: dict = None):
        """Finish logging"""
        self.log_data["status"] = "success" if success else "failed"
        self.log_data["result"] = result or {}
        self.log_data["completed_at"] = datetime.now().isoformat()
        
        # Calculate duration
        start_time = datetime.fromisoformat(
            self.log_data["steps"].get("download", {}).get("timestamp", datetime.now().isoformat())
        )
        end_time = datetime.fromisoformat(self.log_data["completed_at"])
        self.log_data["duration_seconds"] = (end_time - start_time).total_seconds()
        
        self._save()
        
        # Rename file to include status
        if not success:
            error_file = self.log_file.with_name(f"{self.log_file.stem}_ERROR.json")
            self.log_file.rename(error_file)
            self.log_file = error_file
        
        logger.info(f"Finished logging: {self.log_file}")
        return self.log_file
    
    def _save(self):
        """Save log to file"""
        if self.log_file:
            def json_serializer(obj):
                """Convert Path objects to strings for JSON"""
                if isinstance(obj, Path):
                    return str(obj)
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
            
            self.log_file.write_text(
                json.dumps(self.log_data, ensure_ascii=False, indent=2, default=json_serializer),
                encoding='utf-8'
            )
    
    def get_log_path(self) -> Optional[Path]:
        """Get current log file path"""
        return self.log_file
