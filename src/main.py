"""
Instagram Scraper - Main Application
Command-line interface for scraping Instagram followers and following lists
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from auth import InstagramAuth, create_env_file
from scraper import InstagramScraper
from dm_automation import DMAutomation

# Initialize colorama
init(autoreset=True)

class InstagramScraperApp:
    """Main application class for Instagram scraper"""
    
    def __init__(self):
        """Initialize the application"""
        self.auth = InstagramAuth()
        self.scraper = None
        self.dm_automation = None
        self.targets_file = Path("data/targets.json")
        
        # Load environment variables
        load_dotenv()
        
    def load_targets(self) -> Dict:
        """Load targets configuration"""
        try:
            if self.targets_file.exists():
                with open(self.targets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"targets": [], "settings": {}}
        except Exception as e:
            print(f"{Fore.RED}✗ Error loading targets: {str(e)}")
            return {"targets": [], "settings": {}}
    
    def save_targets(self, targets_data: Dict):
        """Save targets configuration"""
        try:
            self.targets_file.parent.mkdir(exist_ok=True)
            with open(self.targets_file, 'w', encoding='utf-8') as f:
                json.dump(targets_data, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}✓ Targets configuration saved")
        except Exception as e:
            print(f"{Fore.RED}✗ Error saving targets: {str(e)}")
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Login to Instagram"""
        # Try to get credentials from environment or prompt
        if not username:
            username = os.getenv('INSTAGRAM_USERNAME')
        if not password:
            password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not username:
            username = input(f"{Fore.CYAN}Enter Instagram username: ")
        if not password:
            password = input(f"{Fore.CYAN}Enter Instagram password: ")
        
        if self.auth.login(username, password):
            self.scraper = InstagramScraper(self.auth)
            self.dm_automation = DMAutomation(self.auth)
            return True
        return False
    
    def scrape_single(self, username: str, max_followers: Optional[int] = None, 
                     max_following: Optional[int] = None) -> Dict:
        """Scrape a single account"""
        if not self.scraper:
            print(f"{Fore.RED}✗ Not logged in. Please login first.")
            return {}
        
        return self.scraper.scrape_account(username, max_followers, max_following)
    
    def scrape_targets(self) -> List[Dict]:
        """Scrape all active targets"""
        if not self.scraper:
            print(f"{Fore.RED}✗ Not logged in. Please login first.")
            return []
        
        targets_data = self.load_targets()
        active_targets = [t for t in targets_data.get('targets', []) if t.get('active', True)]
        
        if not active_targets:
            print(f"{Fore.YELLOW}⚠ No active targets found in configuration")
            return []
        
        results = []
        
        print(f"{Fore.MAGENTA}🎯 Scraping {len(active_targets)} active targets...")
        print("=" * 60)
        
        for i, target in enumerate(active_targets, 1):
            username = target['username']
            max_followers = target.get('max_followers')
            max_following = target.get('max_following')
            
            print(f"{Fore.BLUE}[{i}/{len(active_targets)}] Processing @{username}")
            
            result = self.scraper.scrape_account(username, max_followers, max_following)
            if result:
                # Update last scraped timestamp
                target['last_scraped'] = datetime.now().isoformat()
                results.append(result)
            
            print()
        
        # Save updated targets configuration
        self.save_targets(targets_data)
        
        print(f"{Fore.GREEN}✅ Completed scraping {len(results)} targets")
        return results
    
    def add_target(self, username: str, description: str = "", 
                   max_followers: Optional[int] = None, 
                   max_following: Optional[int] = None):
        """Add a new target to the configuration"""
        targets_data = self.load_targets()
        
        # Check if target already exists
        for target in targets_data.get('targets', []):
            if target['username'].lower() == username.lower():
                print(f"{Fore.YELLOW}⚠ Target @{username} already exists")
                return
        
        new_target = {
            'username': username,
            'description': description,
            'active': True,
            'max_followers': max_followers,
            'max_following': max_following,
            'last_scraped': None
        }
        
        if 'targets' not in targets_data:
            targets_data['targets'] = []
        
        targets_data['targets'].append(new_target)
        self.save_targets(targets_data)
        
        print(f"{Fore.GREEN}✓ Added target @{username}")
    
    def list_targets(self):
        """List all configured targets"""
        targets_data = self.load_targets()
        targets = targets_data.get('targets', [])
        
        if not targets:
            print(f"{Fore.YELLOW}No targets configured")
            return
        
        print(f"{Fore.CYAN}Configured targets:")
        print("-" * 80)
        
        for i, target in enumerate(targets, 1):
            status = "🟢 Active" if target.get('active', True) else "🔴 Inactive"
            last_scraped = target.get('last_scraped', 'Never')
            if last_scraped != 'Never':
                last_scraped = datetime.fromisoformat(last_scraped).strftime('%Y-%m-%d %H:%M')
            
            print(f"{i:2d}. @{target['username']:<20} {status}")
            print(f"    Description: {target.get('description', 'N/A')}")
            print(f"    Limits: {target.get('max_followers', 'All')} followers, {target.get('max_following', 'All')} following")
            print(f"    Last scraped: {last_scraped}")
            print()
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print(f"{Fore.MAGENTA}🔥 Instagram Scraper - Interactive Mode")
        print("=" * 50)
        
        # Login
        if not self.login():
            print(f"{Fore.RED}✗ Login failed. Exiting.")
            return
        
        while True:
            print(f"\n{Fore.CYAN}Choose an option:")
            print("1. Scrape single account")
            print("2. Scrape all active targets")
            print("3. Add new target")
            print("4. List targets")
            print("5. DM Automation Menu")
            print("6. Exit")
            
            choice = input(f"\n{Fore.YELLOW}Enter choice (1-6): ").strip()
            
            try:
                if choice == '1':
                    username = input(f"{Fore.CYAN}Enter username to scrape: ").strip()
                    max_followers = input(f"{Fore.CYAN}Max followers (Enter for all): ").strip()
                    max_following = input(f"{Fore.CYAN}Max following (Enter for all): ").strip()
                    
                    max_followers = int(max_followers) if max_followers else None
                    max_following = int(max_following) if max_following else None
                    
                    self.scrape_single(username, max_followers, max_following)
                
                elif choice == '2':
                    self.scrape_targets()
                
                elif choice == '3':
                    username = input(f"{Fore.CYAN}Enter username: ").strip()
                    description = input(f"{Fore.CYAN}Enter description (optional): ").strip()
                    max_followers = input(f"{Fore.CYAN}Max followers (Enter for all): ").strip()
                    max_following = input(f"{Fore.CYAN}Max following (Enter for all): ").strip()
                    
                    max_followers = int(max_followers) if max_followers else None
                    max_following = int(max_following) if max_following else None
                    
                    self.add_target(username, description, max_followers, max_following)
                
                elif choice == '4':
                    self.list_targets()
                
                elif choice == '5':
                    self.dm_automation_menu()
                
                elif choice == '6':
                    print(f"{Fore.GREEN}👋 Goodbye!")
                    break
                
                else:
                    print(f"{Fore.RED}Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled by user")
            except Exception as e:
                print(f"{Fore.RED}✗ Error: {str(e)}")
        
        # Logout
        self.auth.logout()
    
    def dm_automation_menu(self):
        """DM automation interactive menu"""
        if not self.dm_automation:
            print(f"{Fore.RED}✗ DM automation not initialized")
            return
        
        while True:
            print(f"\n{Fore.MAGENTA}📨 DM Automation Menu")
            print("=" * 40)
            print(f"{Fore.CYAN}1. View DM Statistics")
            print("2. Create DM Template")
            print("3. List DM Templates")
            print("4. Create DM Campaign")
            print("5. List DM Campaigns")
            print("6. Start Campaign")
            print("7. Send Single DM")
            print("8. Block/Unblock User")
            print("9. DM Scraped Accounts")
            print("0. Back to Main Menu")
            
            choice = input(f"\n{Fore.YELLOW}Enter choice (0-9): ").strip()
            
            try:
                if choice == '1':
                    self.show_dm_stats()
                elif choice == '2':
                    self.create_dm_template()
                elif choice == '3':
                    self.list_dm_templates()
                elif choice == '4':
                    self.create_dm_campaign()
                elif choice == '5':
                    self.list_dm_campaigns()
                elif choice == '6':
                    self.start_dm_campaign()
                elif choice == '7':
                    self.send_single_dm()
                elif choice == '8':
                    self.manage_blocked_users()
                elif choice == '9':
                    self.dm_scraped_accounts()
                elif choice == '0':
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please enter 0-9.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled by user")
            except Exception as e:
                print(f"{Fore.RED}✗ Error: {str(e)}")
    
    def show_dm_stats(self):
        """Show DM statistics"""
        stats = self.dm_automation.get_dm_stats()
        print(f"\n{Fore.GREEN}📊 DM Statistics:")
        print(f"Total DMs sent: {stats['total_dms_sent']}")
        print(f"Total DMs failed: {stats['total_dms_failed']}")
        print(f"Today's DMs: {stats['today_dms_sent']}/{stats['daily_limit']}")
        print(f"This hour's DMs: {stats['hourly_remaining']}/{stats['hourly_limit']} remaining")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Active campaigns: {stats['active_campaigns']}")
        print(f"Blocked users: {stats['blocked_users_count']}")
    
    def create_dm_template(self):
        """Create a new DM template"""
        print(f"\n{Fore.CYAN}Creating new DM template...")
        name = input("Template name: ").strip()
        subject = input("Subject: ").strip()
        print("Message (use {username} for username variable):")
        message = input().strip()
        
        variables = ['username']
        template_id = self.dm_automation.create_template(name, subject, message, variables)
        print(f"{Fore.GREEN}✅ Template created with ID: {template_id}")
    
    def list_dm_templates(self):
        """List all DM templates"""
        print(f"\n{Fore.GREEN}📝 DM Templates:")
        for template in self.dm_automation.templates.values():
            status = "✅ Active" if template.active else "❌ Inactive"
            print(f"{template.id}: {template.name} ({status})")
            print(f"   Subject: {template.subject}")
            print(f"   Message: {template.message[:50]}...")
    
    def create_dm_campaign(self):
        """Create a new DM campaign"""
        print(f"\n{Fore.CYAN}Creating new DM campaign...")
        
        # List available templates
        if not self.dm_automation.templates:
            print(f"{Fore.RED}No templates available. Create a template first.")
            return
        
        print("Available templates:")
        for template in self.dm_automation.templates.values():
            print(f"  {template.id}: {template.name}")
        
        template_id = input("Template ID: ").strip()
        if template_id not in self.dm_automation.templates:
            print(f"{Fore.RED}Invalid template ID")
            return
        
        name = input("Campaign name: ").strip()
        
        # Get target list
        print("Enter target usernames (one per line, empty line to finish):")
        targets = []
        while True:
            username = input().strip()
            if not username:
                break
            targets.append(username)
        
        if not targets:
            print(f"{Fore.RED}No targets specified")
            return
        
        campaign_id = self.dm_automation.create_campaign(name, template_id, targets)
        print(f"{Fore.GREEN}✅ Campaign created with ID: {campaign_id}")
    
    def list_dm_campaigns(self):
        """List all DM campaigns"""
        print(f"\n{Fore.GREEN}🎯 DM Campaigns:")
        for campaign in self.dm_automation.campaigns.values():
            print(f"{campaign.id}: {campaign.name} ({campaign.status})")
            print(f"   Targets: {len(campaign.target_list)}")
            print(f"   Sent: {campaign.messages_sent}, Failed: {campaign.messages_failed}")
    
    def start_dm_campaign(self):
        """Start a DM campaign"""
        if not self.dm_automation.campaigns:
            print(f"{Fore.RED}No campaigns available")
            return
        
        print("Available campaigns:")
        for campaign in self.dm_automation.campaigns.values():
            if campaign.status == 'draft':
                print(f"  {campaign.id}: {campaign.name}")
        
        campaign_id = input("Campaign ID to start: ").strip()
        result = self.dm_automation.start_campaign(campaign_id)
        
        if 'error' in result:
            print(f"{Fore.RED}✗ {result['error']}")
        else:
            print(f"{Fore.GREEN}✅ Campaign started")
            
            # Ask if user wants to run it now
            run_now = input("Run campaign now? (y/n): ").strip().lower()
            if run_now == 'y':
                max_msgs = input("Max messages to send (Enter for all): ").strip()
                max_msgs = int(max_msgs) if max_msgs else None
                
                print(f"{Fore.YELLOW}Running campaign...")
                result = self.dm_automation.run_campaign(campaign_id, max_msgs)
                print(f"{Fore.GREEN}✅ Campaign completed:")
                print(f"   Sent: {result['messages_sent']}")
                print(f"   Failed: {result['messages_failed']}")
    
    def send_single_dm(self):
        """Send a single DM"""
        username = input("Target username: ").strip()
        message = input("Message: ").strip()
        
        result = self.dm_automation.send_dm(username, message)
        if result['status'] == 'sent':
            print(f"{Fore.GREEN}✅ DM sent to @{username}")
        else:
            print(f"{Fore.RED}✗ Failed to send DM: {result.get('error', 'Unknown error')}")
    
    def manage_blocked_users(self):
        """Manage blocked users"""
        print(f"\n{Fore.CYAN}Blocked users management:")
        print("1. Block user")
        print("2. Unblock user")
        print("3. List blocked users")
        
        choice = input("Choice (1-3): ").strip()
        
        if choice == '1':
            username = input("Username to block: ").strip()
            self.dm_automation.block_user(username)
            print(f"{Fore.GREEN}✅ User @{username} blocked")
        elif choice == '2':
            username = input("Username to unblock: ").strip()
            self.dm_automation.unblock_user(username)
            print(f"{Fore.GREEN}✅ User @{username} unblocked")
        elif choice == '3':
            blocked = list(self.dm_automation.blocked_users)
            if blocked:
                print(f"Blocked users: {', '.join(blocked)}")
            else:
                print("No blocked users")
    
    def dm_scraped_accounts(self):
        """DM automation for scraped accounts"""
        print(f"\n{Fore.CYAN}DM Scraped Accounts:")
        
        # Load scraped data
        try:
            with open('data/output.json', 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}No scraped data found. Please scrape some accounts first.")
            return
        except Exception as e:
            print(f"{Fore.RED}Error loading scraped data: {str(e)}")
            return
        
        if not scraped_data:
            print(f"{Fore.RED}No scraped data available")
            return
        
        # Show available scraped accounts
        print("Available scraped accounts:")
        for i, account_data in enumerate(scraped_data, 1):
            username = account_data.get('username', 'Unknown')
            followers_count = len(account_data.get('followers', []))
            following_count = len(account_data.get('following', []))
            print(f"  {i}. @{username} - {followers_count} followers, {following_count} following")
        
        choice = input("Select account number (or 'all' for all accounts): ").strip()
        
        if choice.lower() == 'all':
            selected_accounts = scraped_data
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(scraped_data):
                    selected_accounts = [scraped_data[index]]
                else:
                    print(f"{Fore.RED}Invalid selection")
                    return
            except ValueError:
                print(f"{Fore.RED}Invalid input")
                return
        
        # Choose what to DM
        print("\nWhat to DM:")
        print("1. Followers")
        print("2. Following")
        print("3. Both")
        
        dm_choice = input("Choice (1-3): ").strip()
        
        # Collect target usernames
        targets = set()
        for account_data in selected_accounts:
            if dm_choice in ['1', '3']:
                targets.update(account_data.get('followers', []))
            if dm_choice in ['2', '3']:
                targets.update(account_data.get('following', []))
        
        targets = list(targets)
        print(f"Found {len(targets)} unique targets")
        
        # Get template
        if not self.dm_automation.templates:
            print(f"{Fore.RED}No templates available. Create a template first.")
            return
        
        print("Available templates:")
        for template in self.dm_automation.templates.values():
            print(f"  {template.id}: {template.name}")
        
        template_id = input("Template ID: ").strip()
        if template_id not in self.dm_automation.templates:
            print(f"{Fore.RED}Invalid template ID")
            return
        
        # Create campaign
        campaign_name = f"Scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        campaign_id = self.dm_automation.create_campaign(campaign_name, template_id, targets)
        
        print(f"{Fore.GREEN}✅ Campaign created: {campaign_id}")
        
        # Start and run campaign
        start_result = self.dm_automation.start_campaign(campaign_id)
        if 'error' in start_result:
            print(f"{Fore.RED}✗ {start_result['error']}")
            return
        
        max_msgs = input("Max messages to send (Enter for all): ").strip()
        max_msgs = int(max_msgs) if max_msgs else None
        
        print(f"{Fore.YELLOW}Running campaign...")
        result = self.dm_automation.run_campaign(campaign_id, max_msgs)
        
        print(f"{Fore.GREEN}✅ Campaign completed:")
        print(f"   Attempted: {result['messages_attempted']}")
        print(f"   Sent: {result['messages_sent']}")
        print(f"   Failed: {result['messages_failed']}")
        if result.get('stopped_reason'):
            print(f"   Stopped: {result['stopped_reason']}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Instagram Followers/Following Scraper')
    parser.add_argument('--username', '-u', help='Instagram username')
    parser.add_argument('--password', '-p', help='Instagram password')
    parser.add_argument('--target', '-t', help='Target username to scrape')
    parser.add_argument('--max-followers', type=int, help='Maximum followers to scrape')
    parser.add_argument('--max-following', type=int, help='Maximum following to scrape')
    parser.add_argument('--scrape-targets', action='store_true', help='Scrape all active targets')
    parser.add_argument('--add-target', help='Add a new target username')
    parser.add_argument('--list-targets', action='store_true', help='List all configured targets')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--setup', action='store_true', help='Create .env file for credentials')
    
    # DM Automation arguments
    parser.add_argument('--dm-stats', action='store_true', help='Show DM automation statistics')
    parser.add_argument('--dm-scraped', action='store_true', help='Send DMs to scraped accounts')
    parser.add_argument('--dm-user', help='Send single DM to specified user')
    parser.add_argument('--dm-message', help='Message content for single DM')
    parser.add_argument('--dm-template', help='Template ID to use for DM campaign')
    parser.add_argument('--dm-campaign', help='Campaign ID to run')
    
    args = parser.parse_args()
    
    app = InstagramScraperApp()
    
    # Setup mode
    if args.setup:
        create_env_file()
        return
    
    # List targets mode
    if args.list_targets:
        app.list_targets()
        return
    
    # DM stats mode (no login required)
    if args.dm_stats:
        try:
            if not app.login(args.username, args.password):
                print(f"{Fore.RED}✗ Login failed. Exiting.")
                return
            app.show_dm_stats()
            return
        finally:
            app.auth.logout()
    
    # Interactive mode
    if args.interactive:
        app.interactive_mode()
        return
    
    # Login required for other operations
    if not app.login(args.username, args.password):
        print(f"{Fore.RED}✗ Login failed. Exiting.")
        return
    
    try:
        # Add target mode
        if args.add_target:
            app.add_target(args.add_target)
        
        # Scrape targets mode
        elif args.scrape_targets:
            app.scrape_targets()
        
        # Single target mode
        elif args.target:
            app.scrape_single(args.target, args.max_followers, args.max_following)
        
        # DM single user
        elif args.dm_user and args.dm_message:
            result = app.dm_automation.send_dm(args.dm_user, args.dm_message)
            if result['status'] == 'sent':
                print(f"{Fore.GREEN}✅ DM sent to @{args.dm_user}")
            else:
                print(f"{Fore.RED}✗ Failed to send DM: {result.get('error', 'Unknown error')}")
        
        # DM scraped accounts
        elif args.dm_scraped:
            if not args.dm_template:
                print(f"{Fore.RED}✗ Template ID required (--dm-template)")
                return
            
            # Load scraped data and create campaign
            try:
                with open('data/output.json', 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                
                # Collect all followers and following
                targets = set()
                for account_data in scraped_data:
                    targets.update(account_data.get('followers', []))
                    targets.update(account_data.get('following', []))
                
                targets = list(targets)
                if not targets:
                    print(f"{Fore.RED}No targets found in scraped data")
                    return
                
                # Create and run campaign
                campaign_name = f"CLI_Scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                campaign_id = app.dm_automation.create_campaign(campaign_name, args.dm_template, targets)
                
                start_result = app.dm_automation.start_campaign(campaign_id)
                if 'error' in start_result:
                    print(f"{Fore.RED}✗ {start_result['error']}")
                    return
                
                print(f"{Fore.YELLOW}Running DM campaign for {len(targets)} targets...")
                result = app.dm_automation.run_campaign(campaign_id)
                
                print(f"{Fore.GREEN}✅ Campaign completed:")
                print(f"   Sent: {result['messages_sent']}")
                print(f"   Failed: {result['messages_failed']}")
                
            except FileNotFoundError:
                print(f"{Fore.RED}No scraped data found. Please scrape some accounts first.")
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}")
        
        # Run specific campaign
        elif args.dm_campaign:
            result = app.dm_automation.run_campaign(args.dm_campaign)
            if 'error' in result:
                print(f"{Fore.RED}✗ {result['error']}")
            else:
                print(f"{Fore.GREEN}✅ Campaign completed:")
                print(f"   Sent: {result['messages_sent']}")
                print(f"   Failed: {result['messages_failed']}")
        
        else:
            print(f"{Fore.YELLOW}No action specified. Use --help for options or --interactive for interactive mode.")
    
    finally:
        app.auth.logout()


if __name__ == "__main__":
    main()
