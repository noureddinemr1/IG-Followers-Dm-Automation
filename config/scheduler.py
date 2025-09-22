"""
Task Scheduler for Instagram Scraper
Handles scheduled scraping of target accounts
"""

import schedule
import time
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import logging

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from auth import InstagramAuth
from scraper import InstagramScraper
from settings import SETTINGS, get_setting

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(get_setting('output.data_dir')) / 'scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScraperScheduler:
    """Handles scheduled scraping tasks"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.auth = InstagramAuth()
        self.scraper = None
        self.is_running = False
        self.targets_file = Path(get_setting('output.data_dir')) / 'targets.json'
        
    def load_targets(self) -> Dict:
        """Load targets configuration"""
        try:
            if self.targets_file.exists():
                with open(self.targets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"targets": [], "settings": {}}
        except Exception as e:
            logger.error(f"Error loading targets: {str(e)}")
            return {"targets": [], "settings": {}}
    
    def save_targets(self, targets_data: Dict):
        """Save targets configuration"""
        try:
            with open(self.targets_file, 'w', encoding='utf-8') as f:
                json.dump(targets_data, f, indent=2, ensure_ascii=False)
            logger.info("Targets configuration saved")
        except Exception as e:
            logger.error(f"Error saving targets: {str(e)}")
    
    def login(self) -> bool:
        """Login to Instagram using stored credentials"""
        username = get_setting('instagram.username')
        password = get_setting('instagram.password')
        
        if not username or not password:
            logger.error("Instagram credentials not configured")
            return False
        
        try:
            if self.auth.login(username, password):
                self.scraper = InstagramScraper(self.auth)
                logger.info(f"Successfully logged in as {username}")
                return True
            else:
                logger.error("Login failed")
                return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def scrape_targets_job(self):
        """Job function to scrape all active targets"""
        logger.info("Starting scheduled scraping job")
        
        if not self.scraper:
            if not self.login():
                logger.error("Cannot start scraping - login failed")
                return
        
        targets_data = self.load_targets()
        active_targets = [t for t in targets_data.get('targets', []) if t.get('active', True)]
        
        if not active_targets:
            logger.warning("No active targets found")
            return
        
        logger.info(f"Processing {len(active_targets)} active targets")
        
        for target in active_targets:
            username = target['username']
            try:
                logger.info(f"Scraping target: @{username}")
                
                # Check if target should be scraped based on schedule
                if not self._should_scrape_target(target):
                    logger.info(f"Skipping @{username} - not due for scraping")
                    continue
                
                max_followers = target.get('max_followers')
                max_following = target.get('max_following')
                
                result = self.scraper.scrape_account(username, max_followers, max_following)
                
                if result:
                    target['last_scraped'] = datetime.now().isoformat()
                    target['last_success'] = datetime.now().isoformat()
                    target['error_count'] = 0
                    logger.info(f"Successfully scraped @{username}")
                else:
                    target['error_count'] = target.get('error_count', 0) + 1
                    target['last_error'] = datetime.now().isoformat()
                    logger.error(f"Failed to scrape @{username}")
                
                # Disable target if too many errors
                if target.get('error_count', 0) >= 5:
                    target['active'] = False
                    logger.warning(f"Disabled target @{username} due to repeated errors")
                
            except Exception as e:
                logger.error(f"Error scraping @{username}: {str(e)}")
                target['error_count'] = target.get('error_count', 0) + 1
                target['last_error'] = datetime.now().isoformat()
        
        # Save updated targets
        self.save_targets(targets_data)
        logger.info("Scheduled scraping job completed")
    
    def _should_scrape_target(self, target: Dict) -> bool:
        """
        Check if a target should be scraped based on its schedule
        
        Args:
            target: Target configuration dictionary
            
        Returns:
            True if target should be scraped, False otherwise
        """
        last_scraped = target.get('last_scraped')
        if not last_scraped:
            return True  # Never scraped before
        
        try:
            last_scraped_time = datetime.fromisoformat(last_scraped)
            scrape_interval = target.get('scrape_interval_hours', 24)  # Default 24 hours
            
            next_scrape_time = last_scraped_time + timedelta(hours=scrape_interval)
            return datetime.now() >= next_scrape_time
            
        except Exception:
            return True  # If we can't parse the date, scrape anyway
    
    def setup_schedules(self):
        """Setup scheduled jobs"""
        # Daily scraping at 2 AM
        schedule.every().day.at("02:00").do(self.scrape_targets_job)
        
        # Every 6 hours scraping (optional, can be configured)
        # schedule.every(6).hours.do(self.scrape_targets_job)
        
        # Weekly deep scraping on Sundays at 3 AM
        schedule.every().sunday.at("03:00").do(self.weekly_deep_scrape)
        
        logger.info("Scheduled jobs setup completed")
        logger.info("Daily scraping: 02:00")
        logger.info("Weekly deep scraping: Sunday 03:00")
    
    def weekly_deep_scrape(self):
        """Weekly deep scraping with higher limits"""
        logger.info("Starting weekly deep scraping job")
        
        if not self.scraper:
            if not self.login():
                logger.error("Cannot start deep scraping - login failed")
                return
        
        targets_data = self.load_targets()
        active_targets = [t for t in targets_data.get('targets', []) if t.get('active', True)]
        
        for target in active_targets:
            username = target['username']
            try:
                logger.info(f"Deep scraping target: @{username}")
                
                # Use higher limits for deep scraping
                max_followers = target.get('deep_scrape_max_followers', 10000)
                max_following = target.get('deep_scrape_max_following', 10000)
                
                result = self.scraper.scrape_account(username, max_followers, max_following)
                
                if result:
                    target['last_deep_scrape'] = datetime.now().isoformat()
                    logger.info(f"Successfully deep scraped @{username}")
                
            except Exception as e:
                logger.error(f"Error deep scraping @{username}: {str(e)}")
        
        self.save_targets(targets_data)
        logger.info("Weekly deep scraping job completed")
    
    def run(self):
        """Run the scheduler"""
        logger.info("Starting Instagram Scraper Scheduler")
        
        # Initial login
        if not self.login():
            logger.error("Initial login failed - scheduler cannot start")
            return
        
        # Setup schedules
        self.setup_schedules()
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
        finally:
            self.is_running = False
            if self.auth:
                self.auth.logout()
            logger.info("Scheduler shutdown complete")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Scheduler stop requested")
    
    def list_scheduled_jobs(self):
        """List all scheduled jobs"""
        jobs = schedule.get_jobs()
        if not jobs:
            logger.info("No scheduled jobs")
            return
        
        logger.info("Scheduled Jobs:")
        for job in jobs:
            logger.info(f"  - {job}")
    
    def run_manual_scrape(self):
        """Run manual scraping of all targets"""
        logger.info("Running manual scrape of all targets")
        self.scrape_targets_job()


def main():
    """Main entry point for scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Scraper Scheduler')
    parser.add_argument('--run', action='store_true', help='Run the scheduler')
    parser.add_argument('--manual', action='store_true', help='Run manual scrape once')
    parser.add_argument('--list-jobs', action='store_true', help='List scheduled jobs')
    
    args = parser.parse_args()
    
    scheduler = ScraperScheduler()
    
    if args.list_jobs:
        scheduler.setup_schedules()
        scheduler.list_scheduled_jobs()
    elif args.manual:
        scheduler.run_manual_scrape()
    elif args.run:
        scheduler.run()
    else:
        print("Use --run to start scheduler, --manual for one-time scrape, or --list-jobs to see schedule")


if __name__ == "__main__":
    main()
