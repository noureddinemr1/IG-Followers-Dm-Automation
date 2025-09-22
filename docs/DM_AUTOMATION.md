# Instagram DM Automation

This module provides automated direct messaging capabilities for the Instagram Scraper. It allows you to create message templates, manage campaigns, and automatically send DMs to scraped accounts with proper rate limiting and safety features.

## ⚠️ IMPORTANT DISCLAIMERS

**LEGAL AND ETHICAL CONSIDERATIONS:**
1. **Instagram Terms of Service**: Automated messaging may violate Instagram's Terms of Service
2. **Rate Limiting**: The system includes built-in rate limits to avoid triggering Instagram's spam detection
3. **Simulation Mode**: By default, DMs are simulated (not actually sent) to prevent account suspension
4. **User Responsibility**: Users are responsible for compliance with all applicable laws and platform policies

**TECHNICAL LIMITATIONS:**
- Instagram does not provide official API for automated DMs
- Actual DM sending would require browser automation (Selenium) which increases detection risk
- This implementation focuses on campaign management and rate limiting infrastructure

## Features

### 🎯 Campaign Management
- Create reusable message templates with variables
- Organize targets into campaigns
- Track campaign progress and statistics
- Resume interrupted campaigns

### ⚡ Rate Limiting & Safety
- Configurable daily and hourly limits
- Random delays between messages
- Blocked user management
- Comprehensive logging and monitoring

### 📊 Analytics & Reporting
- Real-time campaign statistics
- Success/failure tracking
- Rate limit monitoring
- Comprehensive audit logs

## Quick Start

### 1. Interactive Mode
```bash
python src/main.py --interactive
# Choose option 5: DM Automation Menu
```

### 2. Command Line Usage
```bash
# Show DM statistics
python src/main.py -u your_username -p your_password --dm-stats

# Send DM to scraped accounts using template
python src/main.py -u your_username -p your_password --dm-scraped --dm-template template_1

# Send single DM
python src/main.py -u your_username -p your_password --dm-user target_username --dm-message "Hello!"
```

### 3. API Usage
```bash
# Start the API server
python src/api_service.py

# Access DM endpoints at http://localhost:8080/docs
```

## DM Templates

Templates support variable substitution to personalize messages.

### Creating Templates

**Interactive Mode:**
1. Go to DM Automation Menu → Create DM Template
2. Provide template name, subject, and message
3. Use `{username}` for automatic username substitution

**API:**
```bash
curl -X POST "http://localhost:8080/api/v1/dm/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Introduction Template",
    "subject": "Hello!",
    "message": "Hi {username}! I noticed we have similar interests. Would love to connect! 😊",
    "variables": ["username"]
  }'
```

### Template Variables
- `{username}`: Target's username
- Custom variables can be added for advanced use cases

### Default Templates
The system includes pre-built templates:
- **intro_1**: Basic introduction message
- **business_1**: Business collaboration outreach
- **follow_up**: Follow-up message template

## Campaign Management

### Creating Campaigns

**Requirements:**
- Valid template ID
- List of target usernames
- Optional rate limiting configuration

**Interactive Mode:**
1. Go to DM Automation Menu → Create DM Campaign
2. Select template
3. Enter target usernames (one per line)
4. Campaign is created in 'draft' status

**API:**
```bash
curl -X POST "http://localhost:8080/api/v1/dm/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Outreach Campaign",
    "template_id": "template_123",
    "target_list": ["user1", "user2", "user3"],
    "rate_limit": {
      "messages_per_hour": 5,
      "delay_min": 60,
      "delay_max": 180,
      "daily_limit": 30
    }
  }'
```

### Campaign Lifecycle

1. **Draft**: Campaign created but not started
2. **Active**: Campaign started and ready to run
3. **Completed**: All targets processed
4. **Paused**: Manually paused (future feature)

### Running Campaigns

**Interactive Mode:**
1. Go to DM Automation Menu → Start Campaign
2. Select campaign to start
3. Choose to run immediately or later

**API:**
```bash
# Start campaign
curl -X POST "http://localhost:8080/api/v1/dm/campaigns/{campaign_id}/start"

# Run campaign (send messages)
curl -X POST "http://localhost:8080/api/v1/dm/campaigns/{campaign_id}/run"
```

## Rate Limiting

### Default Limits
- **Daily**: 50 messages per day
- **Hourly**: 10 messages per hour
- **Delay**: 30-120 seconds between messages
- **Retry**: Automatic retry with exponential backoff

### Custom Rate Limiting
```python
custom_limits = {
    "messages_per_hour": 5,    # More conservative
    "delay_min": 60,           # Minimum 1 minute delay
    "delay_max": 300,          # Maximum 5 minute delay
    "daily_limit": 20          # 20 messages per day
}
```

### Safety Features
- Automatic detection of private profiles
- Skip blocked/unavailable users
- Comprehensive error handling
- Rate limit enforcement

## Integration with Scraping

### Auto-DM Scraped Accounts

**Interactive Mode:**
1. First scrape some accounts using the main scraper
2. Go to DM Automation Menu → DM Scraped Accounts
3. Select accounts and choose followers/following
4. Select template and run campaign

**Command Line:**
```bash
# First scrape accounts
python src/main.py -u username -p password --scrape-targets

# Then DM the scraped accounts
python src/main.py -u username -p password --dm-scraped --dm-template intro_1
```

### Data Integration
- Automatically loads from `data/output.json`
- Combines followers and following lists
- Removes duplicates
- Respects blocked user lists

## API Endpoints

### Templates
- `GET /api/v1/dm/templates` - List all templates
- `POST /api/v1/dm/templates` - Create new template

### Campaigns
- `GET /api/v1/dm/campaigns` - List all campaigns
- `POST /api/v1/dm/campaigns` - Create new campaign
- `GET /api/v1/dm/campaigns/{id}/stats` - Get campaign statistics
- `POST /api/v1/dm/campaigns/{id}/start` - Start campaign
- `POST /api/v1/dm/campaigns/{id}/run` - Run campaign

### Direct Messaging
- `POST /api/v1/dm/send` - Send single DM
- `GET /api/v1/dm/stats` - Get overall DM statistics

### User Management
- `POST /api/v1/dm/block/{username}` - Block user
- `POST /api/v1/dm/unblock/{username}` - Unblock user
- `GET /api/v1/dm/blocked-users` - List blocked users

## Configuration

### Environment Variables
```bash
# DM Rate Limiting
DM_DAILY_LIMIT=50
DM_HOURLY_LIMIT=10
DM_MIN_DELAY=30
DM_MAX_DELAY=120

# Safety Settings
DM_SIMULATION_MODE=true  # Set to false for actual sending (NOT RECOMMENDED)
```

### File Locations
- **Templates**: `data/dm_templates.json`
- **Campaigns**: `data/dm_campaigns.json`
- **DM Log**: `data/dm_log.json`
- **Blocked Users**: `data/blocked_users.json`

## Monitoring & Analytics

### Statistics Dashboard
Access comprehensive DM statistics:
- Total messages sent/failed
- Daily/hourly usage
- Success rates
- Active campaigns
- Blocked users count

### Log Analysis
All DM attempts are logged with:
- Timestamp
- Target username
- Message content (truncated)
- Success/failure status
- Error details
- Campaign association

### Prometheus Metrics
- `dm_messages_sent_total`
- `dm_messages_failed_total`
- `dm_campaigns_active`
- `dm_rate_limit_hits_total`

## Troubleshooting

### Common Issues

**"Rate limit reached"**
- Check daily/hourly limits in statistics
- Wait for the next hour/day
- Adjust rate limiting settings

**"Profile not found"**
- Target username doesn't exist
- Username changed
- Account deleted/suspended

**"Cannot DM private user"**
- Target has private profile
- Not following each other
- Consider manual follow first

**"Template not found"**
- Verify template ID exists
- Check template is active
- Recreate template if needed

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python src/main.py --interactive
```

### Data Reset
To reset all DM data:
```bash
rm data/dm_*.json
```

## Best Practices

### 1. Message Quality
- Personalize messages when possible
- Keep messages concise and relevant
- Avoid spammy language
- Include clear value proposition

### 2. Targeting
- Quality over quantity
- Relevant audience only
- Respect user privacy
- Use scraped data responsibly

### 3. Rate Management
- Start with conservative limits
- Monitor success rates
- Adjust based on results
- Respect platform limits

### 4. Compliance
- Review Instagram Terms of Service
- Respect user privacy
- Implement proper consent mechanisms
- Maintain audit logs

## Future Enhancements

### Planned Features
- **A/B Testing**: Test different templates
- **Scheduling**: Time-based campaign execution
- **Advanced Analytics**: Conversion tracking
- **Response Handling**: Auto-reply detection
- **Integration**: CRM and marketing tools

### Technical Improvements
- **Real DM Sending**: Selenium integration (high risk)
- **Machine Learning**: Response prediction
- **Advanced Rate Limiting**: Dynamic adjustment
- **Multi-Account Support**: Account rotation

## Support

### Getting Help
1. Check this documentation
2. Review API documentation (`/docs` endpoint)
3. Check logs in `logs/` directory
4. Review common issues above

### Reporting Issues
When reporting issues, include:
- Error messages
- Log excerpts
- Configuration details
- Steps to reproduce

### Contributing
Contributions welcome for:
- Enhanced rate limiting algorithms
- Better template systems
- Analytics improvements
- Safety features

---

**Remember**: This tool is for educational and research purposes. Always comply with platform terms of service and applicable laws. Use responsibly and ethically.