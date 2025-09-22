"""
Instagram Scraper Module
Handles scraping of followers and following lists from Instagram accounts
"""

import json
import time
import random
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
import instaloader
from tqdm import tqdm
from colorama import Fore, Style, init

from auth import InstagramAuth

# Initialize colorama
init(autoreset=True)

class InstagramScraper:
    """Main scraper class for extracting Instagram followers and following"""
    
    def __init__(self, auth: InstagramAuth, output_dir: str = "data"):
        """
        Initialize the Instagram scraper
        
        Args:
            auth: InstagramAuth instance for authentication
            output_dir: Directory to save scraped data
        """
        self.auth = auth
        self.loader = auth.get_loader()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Rate limiting settings
        self.min_delay = 1  # Minimum delay between requests (seconds)
        self.max_delay = 3  # Maximum delay between requests (seconds)
        self.requests_per_minute = 60  # Maximum requests per minute
        
    def get_profile(self, username: str) -> Optional[instaloader.Profile]:
        """
        Get Instagram profile object
        
        Args:
            username: Instagram username
            
        Returns:
            Profile object if found, None otherwise
        """
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            return profile
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"{Fore.RED}✗ Profile '{username}' not found")
            return None
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"{Fore.YELLOW}⚠ Profile '{username}' is private and you don't follow them")
            return None
        except Exception as e:
            print(f"{Fore.RED}✗ Error accessing profile '{username}': {str(e)}")
            return None
    
    def _rate_limit_delay(self):
        """Apply rate limiting delay"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def get_followers(self, username: str, max_count: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get followers list for a given username
        
        Args:
            username: Instagram username to get followers for
            max_count: Maximum number of followers to retrieve (None for all)
            
        Returns:
            List of follower dictionaries with username and full_name
        """
        print(f"{Fore.BLUE}📥 Getting followers for @{username}...")
        
        profile = self.get_profile(username)
        if not profile:
            return []
        
        followers = []
        count = 0
        
        try:
            # Get total follower count for progress bar
            total_followers = profile.followers
            if max_count:
                total_followers = min(total_followers, max_count)
            
            print(f"{Fore.CYAN}Total followers: {profile.followers:,}")
            if max_count:
                print(f"{Fore.CYAN}Scraping up to: {max_count:,}")
            
            # Create progress bar
            with tqdm(total=total_followers, desc="Followers", unit="users") as pbar:
                for followee in profile.get_followers():
                    if max_count and count >= max_count:
                        break
                    
                    follower_data = {
                        'username': followee.username,
                        'full_name': followee.full_name or '',
                        'is_private': followee.is_private,
                        'is_verified': followee.is_verified,
                        'follower_count': followee.followers,
                        'following_count': followee.followees,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    followers.append(follower_data)
                    count += 1
                    pbar.update(1)
                    
                    # Rate limiting
                    self._rate_limit_delay()
                    
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"{Fore.YELLOW}⚠ Cannot access followers of private profile '{username}'")
        except Exception as e:
            print(f"{Fore.RED}✗ Error getting followers for '{username}': {str(e)}")
        
        print(f"{Fore.GREEN}✓ Retrieved {len(followers):,} followers for @{username}")
        return followers
    
    def get_following(self, username: str, max_count: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get following list for a given username
        
        Args:
            username: Instagram username to get following for
            max_count: Maximum number of following to retrieve (None for all)
            
        Returns:
            List of following dictionaries with username and full_name
        """
        print(f"{Fore.BLUE}📤 Getting following for @{username}...")
        
        profile = self.get_profile(username)
        if not profile:
            return []
        
        following = []
        count = 0
        
        try:
            # Get total following count for progress bar
            total_following = profile.followees
            if max_count:
                total_following = min(total_following, max_count)
            
            print(f"{Fore.CYAN}Total following: {profile.followees:,}")
            if max_count:
                print(f"{Fore.CYAN}Scraping up to: {max_count:,}")
            
            # Create progress bar
            with tqdm(total=total_following, desc="Following", unit="users") as pbar:
                for followee in profile.get_followees():
                    if max_count and count >= max_count:
                        break
                    
                    following_data = {
                        'username': followee.username,
                        'full_name': followee.full_name or '',
                        'is_private': followee.is_private,
                        'is_verified': followee.is_verified,
                        'follower_count': followee.followers,
                        'following_count': followee.followees,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    following.append(following_data)
                    count += 1
                    pbar.update(1)
                    
                    # Rate limiting
                    self._rate_limit_delay()
                    
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"{Fore.YELLOW}⚠ Cannot access following of private profile '{username}'")
        except Exception as e:
            print(f"{Fore.RED}✗ Error getting following for '{username}': {str(e)}")
        
        print(f"{Fore.GREEN}✓ Retrieved {len(following):,} following for @{username}")
        return following
    
    def get_profile_info(self, username: str) -> Optional[Dict]:
        """
        Get detailed profile information
        
        Args:
            username: Instagram username
            
        Returns:
            Dictionary with profile information
        """
        profile = self.get_profile(username)
        if not profile:
            return None
        
        profile_info = {
            'username': profile.username,
            'full_name': profile.full_name or '',
            'biography': profile.biography or '',
            'followers': profile.followers,
            'following': profile.followees,
            'posts': profile.mediacount,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'is_business_account': profile.is_business_account,
            'external_url': profile.external_url or '',
            'scraped_at': datetime.now().isoformat()
        }
        
        return profile_info
    
    def save_data(self, data: List[Dict], filename: str) -> bool:
        """
        Save scraped data to JSON file
        
        Args:
            data: List of dictionaries to save
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.GREEN}✓ Saved {len(data):,} records to {filepath}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error saving data to {filename}: {str(e)}")
            return False
    
    def load_data(self, filename: str) -> List[Dict]:
        """
        Load data from JSON file
        
        Args:
            filename: Input filename
            
        Returns:
            List of dictionaries loaded from file
        """
        try:
            filepath = self.output_dir / filename
            if not filepath.exists():
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"{Fore.GREEN}✓ Loaded {len(data):,} records from {filepath}")
            return data
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error loading data from {filename}: {str(e)}")
            return []
    
    def scrape_account(self, username: str, max_followers: Optional[int] = None, 
                      max_following: Optional[int] = None, 
                      save_files: bool = True) -> Dict:
        """
        Complete scraping of an Instagram account
        
        Args:
            username: Instagram username to scrape
            max_followers: Maximum followers to scrape
            max_following: Maximum following to scrape
            save_files: Whether to save results to files
            
        Returns:
            Dictionary with all scraped data
        """
        print(f"{Fore.MAGENTA}🎯 Starting complete scrape for @{username}")
        print("=" * 50)
        
        # Get profile info
        profile_info = self.get_profile_info(username)
        if not profile_info:
            return {}
        
        print(f"{Fore.CYAN}Profile: {profile_info['full_name']} (@{username})")
        print(f"{Fore.CYAN}Followers: {profile_info['followers']:,}")
        print(f"{Fore.CYAN}Following: {profile_info['following']:,}")
        print(f"{Fore.CYAN}Posts: {profile_info['posts']:,}")
        print("-" * 50)
        
        # Scrape followers
        followers = self.get_followers(username, max_followers)
        print()
        
        # Scrape following
        following = self.get_following(username, max_following)
        print()
        
        # Compile results
        results = {
            'profile': profile_info,
            'followers': followers,
            'following': following,
            'scraped_at': datetime.now().isoformat(),
            'stats': {
                'followers_scraped': len(followers),
                'following_scraped': len(following)
            }
        }
        
        # Save to files if requested
        if save_files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete data
            self.save_data(results, f"{username}_complete_{timestamp}.json")
            
            # Save individual files
            if followers:
                self.save_data(followers, f"{username}_followers_{timestamp}.json")
            if following:
                self.save_data(following, f"{username}_following_{timestamp}.json")
        
        print(f"{Fore.GREEN}✅ Scraping completed for @{username}")
        return results
    
    def compare_lists(self, list1: List[Dict], list2: List[Dict]) -> Dict:
        """
        Compare two user lists to find differences
        
        Args:
            list1: First user list
            list2: Second user list
            
        Returns:
            Dictionary with comparison results
        """
        usernames1 = {user['username'] for user in list1}
        usernames2 = {user['username'] for user in list2}
        
        only_in_first = usernames1 - usernames2
        only_in_second = usernames2 - usernames1
        common = usernames1.intersection(usernames2)
        
        return {
            'only_in_first': list(only_in_first),
            'only_in_second': list(only_in_second),
            'common': list(common),
            'stats': {
                'total_first': len(usernames1),
                'total_second': len(usernames2),
                'only_first': len(only_in_first),
                'only_second': len(only_in_second),
                'common': len(common)
            }
        }


if __name__ == "__main__":
    # Test the scraper
    auth = InstagramAuth()
    
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    
    if auth.login(username, password):
        scraper = InstagramScraper(auth)
        
        target = input("Enter username to scrape: ")
        max_count = input("Max followers/following to scrape (press Enter for all): ")
        
        max_count = int(max_count) if max_count.strip() else None
        
        results = scraper.scrape_account(target, max_count, max_count)
        print(f"\nScraping completed! Check the 'data' folder for results.")
        
        auth.logout()
    else:
        print("Authentication failed.")
