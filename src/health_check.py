"""
Health Check Module for Instagram Scraper
Provides health check endpoints and system monitoring
"""

import os
import sys
import json
import time
import logging
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import redis
import psycopg2
from psycopg2 import sql

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import SETTINGS, get_setting

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check and monitoring class"""
    
    def __init__(self):
        """Initialize health checker"""
        self.start_time = datetime.now()
        self.last_check_time = None
        self.checks = {}
        
    def check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment health"""
        try:
            return {
                "status": "healthy",
                "python_version": sys.version,
                "platform": sys.platform,
                "executable": sys.executable,
                "path": sys.path[:3]  # First 3 entries
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            data_dir = Path(get_setting('output.data_dir', '/app/data'))
            
            # Get disk usage
            usage = psutil.disk_usage(str(data_dir.parent))
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_percent = (usage.used / usage.total) * 100
            
            status = "healthy"
            if free_gb < 1:  # Less than 1GB free
                status = "critical"
            elif used_percent > 90:  # More than 90% used
                status = "warning"
            
            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            status = "healthy"
            if memory.percent > 90:
                status = "critical"
            elif memory.percent > 80:
                status = "warning"
            
            return {
                "status": status,
                "used_percent": memory.percent,
                "available_mb": round(memory.available / (1024**2), 2),
                "total_mb": round(memory.total / (1024**2), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status = "healthy"
            if cpu_percent > 90:
                status = "critical"
            elif cpu_percent > 80:
                status = "warning"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis connection"""
        try:
            # Try to connect to Redis if configured
            redis_host = os.getenv('REDIS_HOST', 'redis')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            
            r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, socket_timeout=5)
            r.ping()
            
            info = r.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_mb": round(info.get('used_memory', 0) / (1024**2), 2),
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_postgres_connection(self) -> Dict[str, Any]:
        """Check PostgreSQL connection"""
        try:
            # Try to connect to PostgreSQL if configured
            db_host = os.getenv('POSTGRES_HOST', 'postgres')
            db_port = os.getenv('POSTGRES_PORT', '5432')
            db_name = os.getenv('POSTGRES_DB', 'instagram_scraper')
            db_user = os.getenv('POSTGRES_USER', 'scraper_user')
            db_password = os.getenv('POSTGRES_PASSWORD', '')
            
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                connect_timeout=5
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT version(), current_database(), current_user;")
                version, database, user = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
                table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "healthy",
                "version": version.split()[1],
                "database": database,
                "user": user,
                "table_count": table_count
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_data_files(self) -> Dict[str, Any]:
        """Check data files and directories"""
        try:
            data_dir = Path(get_setting('output.data_dir', '/app/data'))
            session_dir = Path(get_setting('output.session_dir', '/app/sessions'))
            
            checks = {
                "data_dir_exists": data_dir.exists(),
                "data_dir_writable": os.access(data_dir, os.W_OK) if data_dir.exists() else False,
                "session_dir_exists": session_dir.exists(),
                "session_dir_writable": os.access(session_dir, os.W_OK) if session_dir.exists() else False,
            }
            
            # Count files
            if data_dir.exists():
                json_files = list(data_dir.glob("*.json"))
                checks["json_file_count"] = len(json_files)
                
                # Check recent files (last 24 hours)
                recent_files = []
                for file in json_files:
                    if file.stat().st_mtime > (time.time() - 86400):  # 24 hours
                        recent_files.append(file.name)
                checks["recent_files"] = recent_files[:5]  # Show last 5
            
            status = "healthy"
            if not checks["data_dir_exists"] or not checks["data_dir_writable"]:
                status = "critical"
            elif not checks["session_dir_exists"] or not checks["session_dir_writable"]:
                status = "warning"
            
            return {
                "status": status,
                **checks
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_instagram_session(self) -> Dict[str, Any]:
        """Check Instagram session validity"""
        try:
            from auth import InstagramAuth
            
            # Check if we have valid session files
            session_dir = Path(get_setting('output.session_dir', '/app/sessions'))
            session_files = list(session_dir.glob("*_session*")) if session_dir.exists() else []
            
            status = "healthy"
            if not session_files:
                status = "warning"
                message = "No session files found"
            else:
                # Check if sessions are recent (less than 7 days old)
                recent_sessions = []
                for session_file in session_files:
                    age_days = (time.time() - session_file.stat().st_mtime) / 86400
                    if age_days < 7:
                        recent_sessions.append({
                            "file": session_file.name,
                            "age_days": round(age_days, 2)
                        })
                
                if not recent_sessions:
                    status = "warning"
                    message = "All sessions are older than 7 days"
                else:
                    message = f"Found {len(recent_sessions)} recent sessions"
            
            return {
                "status": status,
                "message": message,
                "session_count": len(session_files),
                "recent_sessions": recent_sessions[:3] if 'recent_sessions' in locals() else []
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            # Application uptime
            uptime = datetime.now() - self.start_time
            
            # Process info
            process = psutil.Process()
            
            return {
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_formatted": str(uptime).split('.')[0],
                "process_id": process.pid,
                "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        self.last_check_time = datetime.now()
        
        checks = {
            "timestamp": self.last_check_time.isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "application": self.get_application_metrics(),
            "system": {
                "python": self.check_python_environment(),
                "disk": self.check_disk_space(),
                "memory": self.check_memory_usage(),
                "cpu": self.check_cpu_usage()
            },
            "services": {
                "redis": self.check_redis_connection(),
                "postgres": self.check_postgres_connection()
            },
            "application_specific": {
                "data_files": self.check_data_files(),
                "instagram_session": self.check_instagram_session()
            }
        }
        
        # Determine overall health status
        all_statuses = []
        
        def extract_statuses(obj):
            if isinstance(obj, dict):
                if 'status' in obj:
                    all_statuses.append(obj['status'])
                for value in obj.values():
                    extract_statuses(value)
        
        extract_statuses(checks)
        
        # Overall status logic
        if 'critical' in all_statuses or 'unhealthy' in all_statuses:
            overall_status = 'unhealthy'
        elif 'warning' in all_statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        checks['overall_status'] = overall_status
        
        # Store checks for metrics
        self.checks = checks
        
        return checks


# Global health checker instance
health_checker = HealthChecker()

def health_check() -> bool:
    """Simple health check function for scripts"""
    try:
        checks = health_checker.run_all_checks()
        return checks['overall_status'] in ['healthy', 'degraded']
    except Exception:
        return False

def get_health_status() -> Dict[str, Any]:
    """Get detailed health status"""
    return health_checker.run_all_checks()

def get_metrics() -> Dict[str, Any]:
    """Get metrics for monitoring systems"""
    checks = health_checker.run_all_checks()
    
    # Convert to metrics format for Prometheus/monitoring
    metrics = {
        "scraper_uptime_seconds": checks['application'].get('uptime_seconds', 0),
        "scraper_memory_usage_mb": checks['application'].get('memory_mb', 0),
        "scraper_cpu_percent": checks['application'].get('cpu_percent', 0),
        "system_memory_percent": checks['system']['memory'].get('used_percent', 0),
        "system_cpu_percent": checks['system']['cpu'].get('cpu_percent', 0),
        "system_disk_percent": 100 - (checks['system']['disk'].get('free_gb', 0) / checks['system']['disk'].get('total_gb', 1) * 100),
        "redis_connected": 1 if checks['services']['redis'].get('status') == 'healthy' else 0,
        "postgres_connected": 1 if checks['services']['postgres'].get('status') == 'healthy' else 0,
        "session_count": checks['application_specific']['instagram_session'].get('session_count', 0),
        "json_file_count": checks['application_specific']['data_files'].get('json_file_count', 0),
        "overall_healthy": 1 if checks['overall_status'] == 'healthy' else 0
    }
    
    return metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Scraper Health Check')
    parser.add_argument('--format', choices=['json', 'prometheus'], default='json', help='Output format')
    parser.add_argument('--simple', action='store_true', help='Simple pass/fail check')
    
    args = parser.parse_args()
    
    if args.simple:
        result = health_check()
        print("HEALTHY" if result else "UNHEALTHY")
        sys.exit(0 if result else 1)
    elif args.format == 'prometheus':
        metrics = get_metrics()
        for key, value in metrics.items():
            print(f"{key} {value}")
    else:
        status = get_health_status()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status['overall_status'] in ['healthy', 'degraded'] else 1)