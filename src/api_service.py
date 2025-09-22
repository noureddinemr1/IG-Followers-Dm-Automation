"""
FastAPI Web Service for Instagram Scraper
Provides REST API endpoints for monitoring, health checks, and management
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from health_check import get_health_status, get_metrics
from logging_config import get_logger, setup_logging
from config.settings import get_setting
from dm_automation import DMAutomation

# Setup logging
logger = get_logger('api')

# Prometheus metrics
REQUEST_COUNT = Counter('scraper_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('scraper_api_request_duration_seconds', 'API request duration')
ACTIVE_SCRAPES = Gauge('scraper_active_scrapes', 'Number of active scraping operations')
TOTAL_SCRAPES = Counter('scraper_total_scrapes', 'Total number of scraping operations', ['status'])

# Pydantic models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Check timestamp")
    checks: Dict[str, Any] = Field(..., description="Detailed health checks")

class MetricsResponse(BaseModel):
    """Metrics response model"""
    metrics: Dict[str, float] = Field(..., description="Application metrics")
    timestamp: str = Field(..., description="Metrics timestamp")

class ScrapeRequest(BaseModel):
    """Scrape request model"""
    username: str = Field(..., description="Instagram username to scrape")
    max_followers: Optional[int] = Field(None, description="Maximum followers to scrape")
    max_following: Optional[int] = Field(None, description="Maximum following to scrape")

class ScrapeResponse(BaseModel):
    """Scrape response model"""
    job_id: str = Field(..., description="Scraping job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")

class JobStatus(BaseModel):
    """Job status model"""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage")
    message: str = Field(..., description="Current message")
    created_at: str = Field(..., description="Job creation time")
    updated_at: str = Field(..., description="Last update time")

# DM Automation Models
class DMTemplateRequest(BaseModel):
    """DM template creation request"""
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Message subject")
    message: str = Field(..., description="Message content with variables")
    variables: List[str] = Field(default=[], description="Available variables")

class DMTemplateResponse(BaseModel):
    """DM template response"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Message subject")
    message: str = Field(..., description="Message content")
    variables: List[str] = Field(..., description="Available variables")
    active: bool = Field(..., description="Template active status")

class DMCampaignRequest(BaseModel):
    """DM campaign creation request"""
    name: str = Field(..., description="Campaign name")
    template_id: str = Field(..., description="Template ID to use")
    target_list: List[str] = Field(..., description="List of target usernames")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Custom rate limiting settings")

class DMCampaignResponse(BaseModel):
    """DM campaign response"""
    id: str = Field(..., description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    template_id: str = Field(..., description="Template ID")
    status: str = Field(..., description="Campaign status")
    target_count: int = Field(..., description="Number of targets")
    messages_sent: int = Field(..., description="Messages sent")
    messages_failed: int = Field(..., description="Messages failed")
    created_at: str = Field(..., description="Creation timestamp")

class DMSendRequest(BaseModel):
    """Single DM send request"""
    username: str = Field(..., description="Target username")
    message: str = Field(..., description="Message content")

class DMStatsResponse(BaseModel):
    """DM statistics response"""
    total_dms_sent: int = Field(..., description="Total DMs sent")
    total_dms_failed: int = Field(..., description="Total DMs failed")
    today_dms_sent: int = Field(..., description="DMs sent today")
    daily_limit: int = Field(..., description="Daily DM limit")
    daily_remaining: int = Field(..., description="Remaining DMs today")
    hourly_limit: int = Field(..., description="Hourly DM limit")
    hourly_remaining: int = Field(..., description="Remaining DMs this hour")
    blocked_users_count: int = Field(..., description="Number of blocked users")
    active_campaigns: int = Field(..., description="Active campaigns")
    total_campaigns: int = Field(..., description="Total campaigns")
    success_rate: float = Field(..., description="Overall success rate")

# Application state
app_state = {
    "scraping_jobs": {},
    "startup_time": datetime.now(),
    "dm_automation": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Instagram Scraper API")
    yield
    # Shutdown
    logger.info("Shutting down Instagram Scraper API")

# Create FastAPI app
app = FastAPI(
    title="Instagram Scraper API",
    description="Production-ready Instagram scraper automation solution",
    version="1.0.0",
    docs_url="/docs" if get_setting('api.docs_enabled', True) else None,
    redoc_url="/redoc" if get_setting('api.docs_enabled', True) else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to collect metrics"""
    start_time = datetime.now()
    
    with REQUEST_DURATION.time():
        response = await call_next(request)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_data = get_health_status()
        return HealthResponse(
            status=health_data['overall_status'],
            timestamp=health_data['timestamp'],
            checks=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )

@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Simple liveness probe for Kubernetes"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Readiness probe for Kubernetes"""
    try:
        health_data = get_health_status()
        if health_data['overall_status'] in ['healthy', 'degraded']:
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

# Metrics endpoints
@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Add custom metrics
        app_metrics = get_metrics()
        
        # Update Prometheus gauges
        for key, value in app_metrics.items():
            if key.startswith('scraper_'):
                # Create or update gauge
                gauge_name = key
                if gauge_name not in globals():
                    globals()[gauge_name] = Gauge(gauge_name, f'Custom metric: {gauge_name}')
                globals()[gauge_name].set(value)
        
        # Generate Prometheus format
        return PlainTextResponse(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Metrics generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics generation failed"
        )

@app.get("/metrics/json", response_model=MetricsResponse, tags=["Monitoring"])
async def json_metrics():
    """JSON metrics endpoint"""
    try:
        metrics_data = get_metrics()
        return MetricsResponse(
            metrics=metrics_data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"JSON metrics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics generation failed"
        )

# Application info endpoints
@app.get("/info", tags=["Info"])
async def app_info():
    """Application information"""
    uptime = datetime.now() - app_state["startup_time"]
    
    return {
        "name": "Instagram Scraper",
        "version": "1.0.0",
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_formatted": str(uptime).split('.')[0],
        "python_version": sys.version,
        "active_jobs": len(app_state["scraping_jobs"])
    }

# Scraping endpoints (basic implementation)
@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start a new scraping job"""
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Job queued for processing",
        "username": request.username,
        "max_followers": request.max_followers,
        "max_following": request.max_following,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    app_state["scraping_jobs"][job_id] = job
    
    # Start background task
    background_tasks.add_task(run_scraping_job, job_id)
    
    TOTAL_SCRAPES.labels(status='started').inc()
    ACTIVE_SCRAPES.inc()
    
    logger.info(f"Started scraping job {job_id} for @{request.username}")
    
    return ScrapeResponse(
        job_id=job_id,
        status="queued",
        message="Scraping job started"
    )

@app.get("/scrape/{job_id}", response_model=JobStatus, tags=["Scraping"])
async def get_job_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in app_state["scraping_jobs"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job = app_state["scraping_jobs"][job_id]
    return JobStatus(**job)

@app.get("/scrape", tags=["Scraping"])
async def list_jobs():
    """List all scraping jobs"""
    return {
        "jobs": list(app_state["scraping_jobs"].values()),
        "total": len(app_state["scraping_jobs"])
    }

async def run_scraping_job(job_id: str):
    """Background task to run scraping job"""
    job = app_state["scraping_jobs"][job_id]
    
    try:
        # Update job status
        job["status"] = "running"
        job["message"] = "Initializing scraper..."
        job["updated_at"] = datetime.now().isoformat()
        
        # Import scraping modules
        from auth import InstagramAuth
        from scraper import InstagramScraper
        
        # Login
        job["message"] = "Logging in to Instagram..."
        job["progress"] = 10.0
        job["updated_at"] = datetime.now().isoformat()
        
        auth = InstagramAuth()
        username = get_setting('instagram.username')
        password = get_setting('instagram.password')
        
        if not auth.login(username, password):
            raise Exception("Instagram login failed")
        
        # Initialize scraper
        job["message"] = "Starting scrape..."
        job["progress"] = 20.0
        job["updated_at"] = datetime.now().isoformat()
        
        scraper = InstagramScraper(auth)
        
        # Run scraping
        result = scraper.scrape_account(
            job["username"],
            job["max_followers"],
            job["max_following"]
        )
        
        if result:
            job["status"] = "completed"
            job["message"] = f"Successfully scraped @{job['username']}"
            job["progress"] = 100.0
            job["result"] = {
                "followers_count": len(result.get('followers', [])),
                "following_count": len(result.get('following', []))
            }
            TOTAL_SCRAPES.labels(status='completed').inc()
        else:
            raise Exception("Scraping failed")
        
        # Logout
        auth.logout()
        
    except Exception as e:
        job["status"] = "failed"
        job["message"] = f"Error: {str(e)}"
        job["progress"] = 0.0
        TOTAL_SCRAPES.labels(status='failed').inc()
        logger.error(f"Scraping job {job_id} failed: {str(e)}")
    
    finally:
        job["updated_at"] = datetime.now().isoformat()
        ACTIVE_SCRAPES.dec()

# Helper function to get DM automation instance
def get_dm_automation():
    """Get or create DM automation instance"""
    if app_state["dm_automation"] is None:
        try:
            from auth import InstagramAuth
            auth = InstagramAuth()
            app_state["dm_automation"] = DMAutomation(auth)
            logger.info("DM automation initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DM automation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DM automation not available"
            )
    return app_state["dm_automation"]

# DM Automation Endpoints

@app.get("/api/v1/dm/stats", response_model=DMStatsResponse)
async def get_dm_stats():
    """Get DM automation statistics"""
    try:
        dm_automation = get_dm_automation()
        stats = dm_automation.get_dm_stats()
        return DMStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting DM stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/templates", response_model=DMTemplateResponse)
async def create_dm_template(template: DMTemplateRequest):
    """Create a new DM template"""
    try:
        dm_automation = get_dm_automation()
        template_id = dm_automation.create_template(
            name=template.name,
            subject=template.subject,
            message=template.message,
            variables=template.variables
        )
        
        created_template = dm_automation.templates[template_id]
        return DMTemplateResponse(
            id=created_template.id,
            name=created_template.name,
            subject=created_template.subject,
            message=created_template.message,
            variables=created_template.variables,
            active=created_template.active
        )
    except Exception as e:
        logger.error(f"Error creating DM template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/dm/templates", response_model=List[DMTemplateResponse])
async def get_dm_templates():
    """Get all DM templates"""
    try:
        dm_automation = get_dm_automation()
        templates = []
        for template in dm_automation.templates.values():
            templates.append(DMTemplateResponse(
                id=template.id,
                name=template.name,
                subject=template.subject,
                message=template.message,
                variables=template.variables,
                active=template.active
            ))
        return templates
    except Exception as e:
        logger.error(f"Error getting DM templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/campaigns", response_model=DMCampaignResponse)
async def create_dm_campaign(campaign: DMCampaignRequest):
    """Create a new DM campaign"""
    try:
        dm_automation = get_dm_automation()
        
        # Validate template exists
        if campaign.template_id not in dm_automation.templates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template not found"
            )
        
        campaign_id = dm_automation.create_campaign(
            name=campaign.name,
            template_id=campaign.template_id,
            target_list=campaign.target_list,
            rate_limit=campaign.rate_limit
        )
        
        created_campaign = dm_automation.campaigns[campaign_id]
        return DMCampaignResponse(
            id=created_campaign.id,
            name=created_campaign.name,
            template_id=created_campaign.template_id,
            status=created_campaign.status,
            target_count=len(created_campaign.target_list),
            messages_sent=created_campaign.messages_sent,
            messages_failed=created_campaign.messages_failed,
            created_at=created_campaign.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating DM campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/dm/campaigns", response_model=List[DMCampaignResponse])
async def get_dm_campaigns():
    """Get all DM campaigns"""
    try:
        dm_automation = get_dm_automation()
        campaigns = []
        for campaign in dm_automation.campaigns.values():
            campaigns.append(DMCampaignResponse(
                id=campaign.id,
                name=campaign.name,
                template_id=campaign.template_id,
                status=campaign.status,
                target_count=len(campaign.target_list),
                messages_sent=campaign.messages_sent,
                messages_failed=campaign.messages_failed,
                created_at=campaign.created_at
            ))
        return campaigns
    except Exception as e:
        logger.error(f"Error getting DM campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/dm/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics"""
    try:
        dm_automation = get_dm_automation()
        stats = dm_automation.get_campaign_stats(campaign_id)
        if 'error' in stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=stats['error']
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/campaigns/{campaign_id}/start")
async def start_dm_campaign(campaign_id: str):
    """Start a DM campaign"""
    try:
        dm_automation = get_dm_automation()
        result = dm_automation.start_campaign(campaign_id)
        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/campaigns/{campaign_id}/run")
async def run_dm_campaign(campaign_id: str, max_messages: Optional[int] = None, background_tasks: BackgroundTasks = None):
    """Run a DM campaign (send messages)"""
    try:
        dm_automation = get_dm_automation()
        
        # Run campaign in background
        if background_tasks:
            background_tasks.add_task(dm_automation.run_campaign, campaign_id, max_messages)
            return {"message": "Campaign started in background", "campaign_id": campaign_id}
        else:
            # Run synchronously (for testing or small campaigns)
            result = dm_automation.run_campaign(campaign_id, max_messages)
            return result
    except Exception as e:
        logger.error(f"Error running campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/send")
async def send_single_dm(dm_request: DMSendRequest):
    """Send a single DM"""
    try:
        dm_automation = get_dm_automation()
        result = dm_automation.send_dm(dm_request.username, dm_request.message)
        return result
    except Exception as e:
        logger.error(f"Error sending DM: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/block/{username}")
async def block_user(username: str):
    """Block a user from receiving DMs"""
    try:
        dm_automation = get_dm_automation()
        dm_automation.block_user(username)
        return {"message": f"User {username} blocked successfully"}
    except Exception as e:
        logger.error(f"Error blocking user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/dm/unblock/{username}")
async def unblock_user(username: str):
    """Unblock a user"""
    try:
        dm_automation = get_dm_automation()
        dm_automation.unblock_user(username)
        return {"message": f"User {username} unblocked successfully"}
    except Exception as e:
        logger.error(f"Error unblocking user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/dm/blocked-users")
async def get_blocked_users():
    """Get list of blocked users"""
    try:
        dm_automation = get_dm_automation()
        return {"blocked_users": list(dm_automation.blocked_users)}
    except Exception as e:
        logger.error(f"Error getting blocked users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    # Setup logging
    setup_logging(enable_console=True)
    
    # Run the application
    port = int(os.getenv('APP_PORT', 8080))
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv('HOT_RELOAD', 'false').lower() == 'true',
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )