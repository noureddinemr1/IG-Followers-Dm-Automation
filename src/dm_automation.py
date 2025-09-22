"""
Instagram DM Automation Module
Handles automated direct messaging to scraped accounts with rate limiting and safety features
"""

import time
import random
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import instaloader
from logging_config import get_logger

logger = get_logger('dm_automation')

@dataclass
class DMTemplate:
    """DM message template"""
    id: str
    name: str
    subject: str
    message: str
    variables: List[str]
    active: bool = True
    
    def render(self, **kwargs) -> str:
        """Render template with variables"""
        message = self.message
        for var, value in kwargs.items():
            if var in self.variables:
                message = message.replace(f"{{{var}}}", str(value))
        return message

@dataclass
class DMCampaign:
    """DM campaign configuration"""
    id: str
    name: str
    template_id: str
    target_list: List[str]
    status: str = "draft"  # draft, active, paused, completed
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    messages_sent: int = 0
    messages_failed: int = 0
    rate_limit: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.rate_limit is None:
            self.rate_limit = {
                "messages_per_hour": 10,
                "delay_min": 30,
                "delay_max": 120,
                "daily_limit": 50
            }

class DMAutomation:
    """Main DM automation class"""
    
    def __init__(self, auth, data_dir: str = "data"):
        """
        Initialize DM automation
        
        Args:
            auth: InstagramAuth instance
            data_dir: Directory for data storage
        """
        self.auth = auth
        self.loader = auth.get_loader()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # DM tracking
        self.dm_log_file = self.data_dir / "dm_log.json"
        self.templates_file = self.data_dir / "dm_templates.json"
        self.campaigns_file = self.data_dir / "dm_campaigns.json"
        self.blocked_users_file = self.data_dir / "blocked_users.json"
        
        # Rate limiting
        self.daily_dm_count = 0
        self.hourly_dm_count = 0
        self.last_dm_time = None
        self.last_hour_reset = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Safety limits
        self.max_daily_dms = 50
        self.max_hourly_dms = 10
        self.min_delay = 30  # seconds
        self.max_delay = 120  # seconds
        
        # Load existing data
        self._load_dm_log()
        self._load_templates()
        self._load_campaigns()
        self._load_blocked_users()
    
    def _load_dm_log(self) -> List[Dict]:
        """Load DM log from file"""
        try:
            if self.dm_log_file.exists():
                with open(self.dm_log_file, 'r', encoding='utf-8') as f:
                    self.dm_log = json.load(f)
            else:
                self.dm_log = []
            
            # Count today's DMs
            today = datetime.now().date().isoformat()
            self.daily_dm_count = len([
                dm for dm in self.dm_log 
                if dm.get('sent_at', '').startswith(today) and dm.get('status') == 'sent'
            ])
            
            # Count this hour's DMs
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            self.hourly_dm_count = len([
                dm for dm in self.dm_log 
                if dm.get('sent_at', '') >= current_hour.isoformat() and dm.get('status') == 'sent'
            ])
            
            logger.info(f"Loaded DM log: {len(self.dm_log)} total, {self.daily_dm_count} today, {self.hourly_dm_count} this hour")
            
        except Exception as e:
            logger.error(f"Error loading DM log: {str(e)}")
            self.dm_log = []
            self.daily_dm_count = 0
            self.hourly_dm_count = 0
    
    def _save_dm_log(self):
        """Save DM log to file"""
        try:
            with open(self.dm_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.dm_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving DM log: {str(e)}")
    
    def _load_templates(self):
        """Load DM templates"""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = {
                        t['id']: DMTemplate(**t) for t in data
                    }
            else:
                self.templates = {}
                self._create_default_templates()
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
            self.templates = {}
    
    def _save_templates(self):
        """Save templates to file"""
        try:
            data = [
                {
                    'id': t.id,
                    'name': t.name,
                    'subject': t.subject,
                    'message': t.message,
                    'variables': t.variables,
                    'active': t.active
                }
                for t in self.templates.values()
            ]
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving templates: {str(e)}")
    
    def _load_campaigns(self):
        """Load DM campaigns"""
        try:
            if self.campaigns_file.exists():
                with open(self.campaigns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.campaigns = {
                        c['id']: DMCampaign(**c) for c in data
                    }
            else:
                self.campaigns = {}
        except Exception as e:
            logger.error(f"Error loading campaigns: {str(e)}")
            self.campaigns = {}
    
    def _save_campaigns(self):
        """Save campaigns to file"""
        try:
            data = [
                {
                    'id': c.id,
                    'name': c.name,
                    'template_id': c.template_id,
                    'target_list': c.target_list,
                    'status': c.status,
                    'created_at': c.created_at,
                    'started_at': c.started_at,
                    'completed_at': c.completed_at,
                    'messages_sent': c.messages_sent,
                    'messages_failed': c.messages_failed,
                    'rate_limit': c.rate_limit
                }
                for c in self.campaigns.values()
            ]
            with open(self.campaigns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving campaigns: {str(e)}")
    
    def _load_blocked_users(self):
        """Load blocked users list"""
        try:
            if self.blocked_users_file.exists():
                with open(self.blocked_users_file, 'r', encoding='utf-8') as f:
                    self.blocked_users = set(json.load(f))
            else:
                self.blocked_users = set()
        except Exception as e:
            logger.error(f"Error loading blocked users: {str(e)}")
            self.blocked_users = set()
    
    def _save_blocked_users(self):
        """Save blocked users list"""
        try:
            with open(self.blocked_users_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blocked_users), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving blocked users: {str(e)}")
    
    def _create_default_templates(self):
        """Create default DM templates"""
        default_templates = [
            DMTemplate(
                id="intro_1",
                name="Introduction Template 1",
                subject="Hello!",
                message="Hi {username}! I noticed we have similar interests. Would love to connect! 😊",
                variables=["username"]
            ),
            DMTemplate(
                id="business_1",
                name="Business Outreach",
                subject="Collaboration Opportunity",
                message="Hello {username}! I love your content about {topic}. I have a collaboration opportunity that might interest you. Would you be open to a quick chat?",
                variables=["username", "topic"]
            ),
            DMTemplate(
                id="follow_up",
                name="Follow-up Message",
                subject="Follow-up",
                message="Hi {username}! Just following up on my previous message. Hope you're having a great day!",
                variables=["username"]
            )
        ]
        
        for template in default_templates:
            self.templates[template.id] = template
        
        self._save_templates()
        logger.info(f"Created {len(default_templates)} default templates")
    
    def can_send_dm(self) -> tuple[bool, str]:
        """Check if we can send a DM based on rate limits"""
        now = datetime.now()
        
        # Check if we need to reset hourly counter
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        if current_hour > self.last_hour_reset:
            self.hourly_dm_count = 0
            self.last_hour_reset = current_hour
        
        # Check daily limit
        if self.daily_dm_count >= self.max_daily_dms:
            return False, f"Daily limit reached ({self.max_daily_dms})"
        
        # Check hourly limit
        if self.hourly_dm_count >= self.max_hourly_dms:
            return False, f"Hourly limit reached ({self.max_hourly_dms})"
        
        # Check minimum delay
        if self.last_dm_time:
            time_since_last = (now - self.last_dm_time).total_seconds()
            if time_since_last < self.min_delay:
                return False, f"Must wait {self.min_delay - time_since_last:.0f} more seconds"
        
        return True, "OK"
    
    def send_dm(self, username: str, message: str, campaign_id: str = None) -> Dict[str, Any]:
        """
        Send a direct message to a user
        
        Args:
            username: Target username
            message: Message content
            campaign_id: Optional campaign ID
            
        Returns:
            Result dictionary with status and details
        """
        result = {
            'username': username,
            'message': message,
            'campaign_id': campaign_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error': None
        }
        
        try:
            # Check if user is blocked
            if username in self.blocked_users:
                result['error'] = "User is blocked"
                logger.warning(f"Attempted to DM blocked user: {username}")
                return result
            
            # Check rate limits
            can_send, reason = self.can_send_dm()
            if not can_send:
                result['error'] = f"Rate limit: {reason}"
                logger.warning(f"Rate limit prevents DM to {username}: {reason}")
                return result
            
            # Get user profile
            try:
                profile = instaloader.Profile.from_username(self.loader.context, username)
            except instaloader.exceptions.ProfileNotExistsException:
                result['error'] = "Profile not found"
                logger.warning(f"Profile not found: {username}")
                return result
            except instaloader.exceptions.PrivateProfileNotFollowedException:
                result['error'] = "Private profile not followed"
                logger.warning(f"Cannot DM private profile: {username}")
                return result
            
            # Check if we can DM this user (mutual follow, etc.)
            if profile.is_private and not profile.followed_by_viewer:
                result['error'] = "Cannot DM private user we don't follow"
                logger.warning(f"Cannot DM private user: {username}")
                return result
            
            # Simulate sending DM (Instagram's API doesn't allow automated DMs)
            # In a real implementation, you would use selenium or other automation
            logger.info(f"Simulating DM send to {username}: {message[:50]}...")
            
            # Apply rate limiting delay
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)
            
            # Mark as sent (simulation)
            result['status'] = 'sent'
            result['delay_applied'] = delay
            
            # Update counters
            self.daily_dm_count += 1
            self.hourly_dm_count += 1
            self.last_dm_time = datetime.now()
            
            # Log the DM
            self.dm_log.append(result.copy())
            self._save_dm_log()
            
            logger.info(f"DM sent to {username} (simulation)")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error sending DM to {username}: {str(e)}")
        
        return result
    
    def create_template(self, name: str, subject: str, message: str, variables: List[str] = None) -> str:
        """Create a new DM template"""
        template_id = f"template_{int(time.time())}"
        template = DMTemplate(
            id=template_id,
            name=name,
            subject=subject,
            message=message,
            variables=variables or []
        )
        
        self.templates[template_id] = template
        self._save_templates()
        
        logger.info(f"Created template: {name} ({template_id})")
        return template_id
    
    def create_campaign(self, name: str, template_id: str, target_list: List[str], 
                       rate_limit: Dict[str, Any] = None) -> str:
        """Create a new DM campaign"""
        campaign_id = f"campaign_{int(time.time())}"
        campaign = DMCampaign(
            id=campaign_id,
            name=name,
            template_id=template_id,
            target_list=target_list,
            rate_limit=rate_limit
        )
        
        self.campaigns[campaign_id] = campaign
        self._save_campaigns()
        
        logger.info(f"Created campaign: {name} ({campaign_id}) with {len(target_list)} targets")
        return campaign_id
    
    def start_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Start a DM campaign"""
        if campaign_id not in self.campaigns:
            return {'error': 'Campaign not found'}
        
        campaign = self.campaigns[campaign_id]
        if campaign.status != 'draft':
            return {'error': f'Campaign is already {campaign.status}'}
        
        if campaign.template_id not in self.templates:
            return {'error': 'Template not found'}
        
        template = self.templates[campaign.template_id]
        if not template.active:
            return {'error': 'Template is not active'}
        
        # Start campaign
        campaign.status = 'active'
        campaign.started_at = datetime.now().isoformat()
        self._save_campaigns()
        
        logger.info(f"Started campaign: {campaign.name} ({campaign_id})")
        
        return {
            'campaign_id': campaign_id,
            'status': 'started',
            'targets': len(campaign.target_list),
            'template': template.name
        }
    
    def run_campaign(self, campaign_id: str, max_messages: int = None) -> Dict[str, Any]:
        """Run a campaign and send DMs"""
        if campaign_id not in self.campaigns:
            return {'error': 'Campaign not found'}
        
        campaign = self.campaigns[campaign_id]
        if campaign.status != 'active':
            return {'error': f'Campaign is not active (status: {campaign.status})'}
        
        template = self.templates[campaign.template_id]
        results = {
            'campaign_id': campaign_id,
            'messages_attempted': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'errors': [],
            'stopped_reason': None
        }
        
        # Get remaining targets (not yet contacted)
        sent_usernames = {
            dm['username'] for dm in self.dm_log 
            if dm.get('campaign_id') == campaign_id and dm.get('status') == 'sent'
        }
        remaining_targets = [u for u in campaign.target_list if u not in sent_usernames]
        
        logger.info(f"Running campaign {campaign_id}: {len(remaining_targets)} remaining targets")
        
        for username in remaining_targets:
            if max_messages and results['messages_attempted'] >= max_messages:
                results['stopped_reason'] = 'Max messages limit reached'
                break
            
            # Check if we can still send
            can_send, reason = self.can_send_dm()
            if not can_send:
                results['stopped_reason'] = f'Rate limit: {reason}'
                break
            
            # Render message with variables
            try:
                message = template.render(username=username)
            except Exception as e:
                logger.error(f"Template render error for {username}: {str(e)}")
                results['errors'].append(f"{username}: Template render error")
                continue
            
            # Send DM
            dm_result = self.send_dm(username, message, campaign_id)
            results['messages_attempted'] += 1
            
            if dm_result['status'] == 'sent':
                results['messages_sent'] += 1
                campaign.messages_sent += 1
            else:
                results['messages_failed'] += 1
                campaign.messages_failed += 1
                results['errors'].append(f"{username}: {dm_result.get('error', 'Unknown error')}")
        
        # Update campaign status
        if not remaining_targets or results['stopped_reason'] == 'Max messages limit reached':
            campaign.status = 'completed'
            campaign.completed_at = datetime.now().isoformat()
        
        self._save_campaigns()
        
        logger.info(f"Campaign run completed: {results['messages_sent']} sent, {results['messages_failed']} failed")
        
        return results
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        if campaign_id not in self.campaigns:
            return {'error': 'Campaign not found'}
        
        campaign = self.campaigns[campaign_id]
        
        # Count DMs from log
        campaign_dms = [
            dm for dm in self.dm_log 
            if dm.get('campaign_id') == campaign_id
        ]
        
        sent_count = len([dm for dm in campaign_dms if dm.get('status') == 'sent'])
        failed_count = len([dm for dm in campaign_dms if dm.get('status') == 'failed'])
        
        return {
            'campaign_id': campaign_id,
            'name': campaign.name,
            'status': campaign.status,
            'total_targets': len(campaign.target_list),
            'messages_sent': sent_count,
            'messages_failed': failed_count,
            'remaining_targets': len(campaign.target_list) - sent_count,
            'success_rate': (sent_count / len(campaign.target_list) * 100) if campaign.target_list else 0,
            'created_at': campaign.created_at,
            'started_at': campaign.started_at,
            'completed_at': campaign.completed_at
        }
    
    def block_user(self, username: str):
        """Add user to blocked list"""
        self.blocked_users.add(username)
        self._save_blocked_users()
        logger.info(f"Blocked user: {username}")
    
    def unblock_user(self, username: str):
        """Remove user from blocked list"""
        self.blocked_users.discard(username)
        self._save_blocked_users()
        logger.info(f"Unblocked user: {username}")
    
    def get_dm_stats(self) -> Dict[str, Any]:
        """Get overall DM statistics"""
        today = datetime.now().date().isoformat()
        
        total_sent = len([dm for dm in self.dm_log if dm.get('status') == 'sent'])
        total_failed = len([dm for dm in self.dm_log if dm.get('status') == 'failed'])
        today_sent = len([
            dm for dm in self.dm_log 
            if dm.get('sent_at', '').startswith(today) and dm.get('status') == 'sent'
        ])
        
        return {
            'total_dms_sent': total_sent,
            'total_dms_failed': total_failed,
            'today_dms_sent': today_sent,
            'daily_limit': self.max_daily_dms,
            'daily_remaining': self.max_daily_dms - self.daily_dm_count,
            'hourly_limit': self.max_hourly_dms,
            'hourly_remaining': self.max_hourly_dms - self.hourly_dm_count,
            'blocked_users_count': len(self.blocked_users),
            'active_campaigns': len([c for c in self.campaigns.values() if c.status == 'active']),
            'total_campaigns': len(self.campaigns),
            'success_rate': (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
        }