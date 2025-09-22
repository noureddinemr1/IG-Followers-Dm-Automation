# API Documentation

## Overview

The Instagram Scraper provides a RESTful API built with FastAPI for programmatic access to scraping functionality, health monitoring, and system metrics.

## Base URL

```
http://localhost:8080
```

## Authentication

Currently, the API does not require authentication for basic endpoints. For production deployments, consider implementing API key authentication or OAuth2.

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "status": "success|error",
  "data": {},
  "message": "Human readable message",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Endpoints

### Health Check Endpoints

#### GET /health
Comprehensive health check including all system components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "checks": {
    "overall_status": "healthy",
    "system": {
      "python": {"status": "healthy"},
      "disk": {"status": "healthy", "free_gb": 45.2},
      "memory": {"status": "healthy", "used_percent": 65.2},
      "cpu": {"status": "healthy", "cpu_percent": 15.3}
    },
    "services": {
      "redis": {"status": "healthy"},
      "postgres": {"status": "healthy"}
    }
  }
}
```

#### GET /health/live
Simple liveness probe for container orchestration.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### GET /health/ready
Readiness probe for container orchestration.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Monitoring Endpoints

#### GET /metrics
Prometheus-formatted metrics for monitoring systems.

**Response:**
```
# HELP scraper_uptime_seconds Application uptime
# TYPE scraper_uptime_seconds gauge
scraper_uptime_seconds 3600
# HELP scraper_memory_usage_mb Memory usage in MB
# TYPE scraper_memory_usage_mb gauge
scraper_memory_usage_mb 256.5
```

#### GET /metrics/json
JSON-formatted metrics for programmatic access.

**Response:**
```json
{
  "metrics": {
    "scraper_uptime_seconds": 3600,
    "scraper_memory_usage_mb": 256.5,
    "scraper_cpu_percent": 15.3,
    "system_memory_percent": 65.2,
    "redis_connected": 1,
    "postgres_connected": 1
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Application Info

#### GET /info
Application information and runtime details.

**Response:**
```json
{
  "name": "Instagram Scraper",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600,
  "uptime_formatted": "1:00:00",
  "python_version": "3.11.5",
  "active_jobs": 2
}
```

### Scraping Endpoints

#### POST /scrape
Start a new scraping job.

**Request Body:**
```json
{
  "username": "target_account",
  "max_followers": 1000,
  "max_following": 500
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Scraping job started"
}
```

#### GET /scrape/{job_id}
Get the status of a specific scraping job.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 45.0,
  "message": "Scraping followers...",
  "username": "target_account",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:02:30Z"
}
```

**Job Status Values:**
- `queued`: Job is waiting to be processed
- `running`: Job is currently being executed
- `completed`: Job finished successfully
- `failed`: Job encountered an error

#### GET /scrape
List all scraping jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "progress": 100.0,
      "message": "Successfully scraped @target_account",
      "username": "target_account",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:05:00Z"
    }
  ],
  "total": 1
}
```

### DM Automation Endpoints

#### GET /api/v1/dm/stats
Get comprehensive DM automation statistics.

**Response:**
```json
{
  "total_dms_sent": 145,
  "total_dms_failed": 12,
  "today_dms_sent": 23,
  "daily_limit": 50,
  "daily_remaining": 27,
  "hourly_limit": 10,
  "hourly_remaining": 7,
  "blocked_users_count": 3,
  "active_campaigns": 2,
  "total_campaigns": 5,
  "success_rate": 92.4
}
```

#### POST /api/v1/dm/templates
Create a new DM template.

**Request Body:**
```json
{
  "name": "Introduction Template",
  "subject": "Hello!",
  "message": "Hi {username}! I noticed we have similar interests. Would love to connect! 😊",
  "variables": ["username"]
}
```

**Response:**
```json
{
  "id": "template_1234567890",
  "name": "Introduction Template",
  "subject": "Hello!",
  "message": "Hi {username}! I noticed we have similar interests. Would love to connect! 😊",
  "variables": ["username"],
  "active": true
}
```

#### GET /api/v1/dm/templates
List all DM templates.

**Response:**
```json
[
  {
    "id": "intro_1",
    "name": "Introduction Template 1",
    "subject": "Hello!",
    "message": "Hi {username}! I noticed we have similar interests. Would love to connect! 😊",
    "variables": ["username"],
    "active": true
  }
]
```

#### POST /api/v1/dm/campaigns
Create a new DM campaign.

**Request Body:**
```json
{
  "name": "Q4 Outreach Campaign",
  "template_id": "intro_1",
  "target_list": ["user1", "user2", "user3"],
  "rate_limit": {
    "messages_per_hour": 5,
    "delay_min": 60,
    "delay_max": 180,
    "daily_limit": 30
  }
}
```

**Response:**
```json
{
  "id": "campaign_1234567890",
  "name": "Q4 Outreach Campaign",
  "template_id": "intro_1",
  "status": "draft",
  "target_count": 3,
  "messages_sent": 0,
  "messages_failed": 0,
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### GET /api/v1/dm/campaigns
List all DM campaigns.

**Response:**
```json
[
  {
    "id": "campaign_1234567890",
    "name": "Q4 Outreach Campaign",
    "template_id": "intro_1",
    "status": "active",
    "target_count": 100,
    "messages_sent": 45,
    "messages_failed": 3,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

#### GET /api/v1/dm/campaigns/{campaign_id}/stats
Get detailed statistics for a specific campaign.

**Response:**
```json
{
  "campaign_id": "campaign_1234567890",
  "name": "Q4 Outreach Campaign",
  "status": "active",
  "total_targets": 100,
  "messages_sent": 45,
  "messages_failed": 3,
  "remaining_targets": 52,
  "success_rate": 93.75,
  "created_at": "2024-01-01T10:00:00Z",
  "started_at": "2024-01-01T11:00:00Z",
  "completed_at": null
}
```

#### POST /api/v1/dm/campaigns/{campaign_id}/start
Start a DM campaign (change status from draft to active).

**Response:**
```json
{
  "campaign_id": "campaign_1234567890",
  "status": "started",
  "targets": 100,
  "template": "Introduction Template 1"
}
```

#### POST /api/v1/dm/campaigns/{campaign_id}/run
Execute a DM campaign (send messages).

**Query Parameters:**
- `max_messages` (optional): Maximum number of messages to send in this run

**Response:**
```json
{
  "campaign_id": "campaign_1234567890",
  "messages_attempted": 10,
  "messages_sent": 8,
  "messages_failed": 2,
  "errors": [
    "user3: Profile not found",
    "user7: Cannot DM private user we don't follow"
  ],
  "stopped_reason": "Rate limit: Hourly limit reached (10)"
}
```

#### POST /api/v1/dm/send
Send a single DM to a user.

**Request Body:**
```json
{
  "username": "target_user",
  "message": "Hello! I found your profile interesting and would love to connect."
}
```

**Response:**
```json
{
  "username": "target_user",
  "message": "Hello! I found your profile interesting and would love to connect.",
  "campaign_id": null,
  "timestamp": "2024-01-01T10:00:00Z",
  "status": "sent",
  "error": null
}
```

#### POST /api/v1/dm/block/{username}
Block a user from receiving DMs.

**Response:**
```json
{
  "message": "User target_user blocked successfully"
}
```

#### POST /api/v1/dm/unblock/{username}
Unblock a user.

**Response:**
```json
{
  "message": "User target_user unblocked successfully"
}
```

#### GET /api/v1/dm/blocked-users
Get list of blocked users.

**Response:**
```json
{
  "blocked_users": ["spam_user1", "spam_user2", "reported_user"]
}
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Rate Limit**: 100 requests per minute per IP
- **Headers**: Rate limit information included in response headers
- **429 Status**: Returned when rate limit exceeded

## Examples

### Python Client Example

```python
import requests
import time

# Start scraping job
response = requests.post('http://localhost:8080/scrape', json={
    'username': 'target_account',
    'max_followers': 1000
})

job_data = response.json()
job_id = job_data['job_id']

# Poll for completion
while True:
    response = requests.get(f'http://localhost:8080/scrape/{job_id}')
    job_status = response.json()
    
    if job_status['status'] in ['completed', 'failed']:
        break
    
    print(f"Progress: {job_status['progress']:.1f}%")
    time.sleep(10)

print(f"Job finished with status: {job_status['status']}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# Start scraping job
curl -X POST http://localhost:8080/scrape \
  -H "Content-Type: application/json" \
  -d '{"username": "target_account", "max_followers": 1000}'

# Check job status
curl http://localhost:8080/scrape/123e4567-e89b-12d3-a456-426614174000

# Get metrics
curl http://localhost:8080/metrics/json
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function scrapeAccount(username, maxFollowers = 1000) {
  try {
    // Start scraping job
    const startResponse = await axios.post('http://localhost:8080/scrape', {
      username: username,
      max_followers: maxFollowers
    });
    
    const jobId = startResponse.data.job_id;
    console.log(`Started job: ${jobId}`);
    
    // Poll for completion
    while (true) {
      const statusResponse = await axios.get(`http://localhost:8080/scrape/${jobId}`);
      const jobStatus = statusResponse.data;
      
      console.log(`Progress: ${jobStatus.progress}% - ${jobStatus.message}`);
      
      if (jobStatus.status === 'completed') {
        console.log('Scraping completed successfully!');
        break;
      } else if (jobStatus.status === 'failed') {
        console.error('Scraping failed:', jobStatus.message);
        break;
      }
      
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
    }
    
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Usage
scrapeAccount('target_account', 1000);
```

## WebSocket Support (Future Enhancement)

Real-time job progress updates via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/scrape/123e4567-e89b-12d3-a456-426614174000');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress}% - ${update.message}`);
};
```

## SDK Libraries

### Python SDK

```python
from instagram_scraper_client import ScraperClient

client = ScraperClient('http://localhost:8080')

# Start scraping
job = client.scrape('target_account', max_followers=1000)

# Wait for completion
result = job.wait_for_completion()
print(f"Scraped {result.followers_count} followers")
```

### Node.js SDK

```javascript
const { ScraperClient } = require('instagram-scraper-client');

const client = new ScraperClient('http://localhost:8080');

async function main() {
  const job = await client.scrape('target_account', { maxFollowers: 1000 });
  const result = await job.waitForCompletion();
  console.log(`Scraped ${result.followersCount} followers`);
}
```

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI JSON**: `http://localhost:8080/openapi.json`