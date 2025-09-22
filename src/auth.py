"""
Instagram Authentication Module
Handles login and session management for Instagram scraping
"""

import os
import pickle
import time
from pathlib import Path
from typing import Optional
import instaloader
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

class InstagramAuth:
    
    def __init__(self, session_dir: str = "sessions"):
        """
        Initialize Instagram authentication
        session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )
        
    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram
        
        Args:
            username: Instagram username
            password: Instagram password
            
        Returns:
            True if login successful, False otherwise
        """
        session_file = self.session_dir / f"{username}_session"
        
        try:
            # Try to load existing session
            if session_file.exists():
                print(f"{Fore.YELLOW}Loading existing session for {username}...")
                self.loader.load_session_from_file(username, str(session_file))
                
                # Test if session is still valid
                if self._test_session():
                    print(f"{Fore.GREEN}✓ Session loaded successfully!")
                    return True
                else:
                    print(f"{Fore.YELLOW}Session expired, logging in again...")
                    session_file.unlink(missing_ok=True)
            
            # Login with credentials
            print(f"{Fore.BLUE}Logging in as {username}...")
            self.loader.login(username, password)
            
            # Save session
            self.loader.save_session_to_file(str(session_file))
            print(f"{Fore.GREEN}✓ Login successful! Session saved.")
            
            return True
            
        except instaloader.exceptions.BadCredentialsException:
            print(f"{Fore.RED}✗ Invalid credentials for {username}")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            print(f"{Fore.YELLOW}Two-factor authentication required for {username}")
            return self._handle_2fa(username, session_file)
        except Exception as e:
            print(f"{Fore.RED}✗ Login failed: {str(e)}")
            return False
    
    def _handle_2fa(self, username: str, session_file: Path) -> bool:
        """
        Handle two-factor authentication
        
        Args:
            username: Instagram username
            session_file: Path to session file
            
        Returns:
            True if 2FA successful, False otherwise
        """
        try:
            # Prompt for 2FA code
            code = input(f"{Fore.CYAN}Enter 2FA code for {username}: ").strip()
            
            # Complete 2FA
            self.loader.two_factor_login(code)
            
            # Save session
            self.loader.save_session_to_file(str(session_file))
            print(f"{Fore.GREEN}✓ 2FA successful! Session saved.")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ 2FA failed: {str(e)}")
            return False
    
    def _test_session(self) -> bool:
        """
        Test if current session is valid
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            # Try to access own profile to test session
            profile = instaloader.Profile.from_username(
                self.loader.context, 
                self.loader.context.username
            )
            return True
        except:
            return False
    
    def logout(self):
        """Logout and clear session"""
        try:
            username = self.loader.context.username
            if username:
                session_file = self.session_dir / f"{username}_session"
                session_file.unlink(missing_ok=True)
                print(f"{Fore.GREEN}✓ Logged out and session cleared for {username}")
        except:
            pass
    
    def is_logged_in(self) -> bool:
        """
        Check if user is currently logged in
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            return self.loader.context.username is not None
        except:
            return False
    
    def get_username(self) -> Optional[str]:
        """
        Get current logged in username
        
        Returns:
            Username if logged in, None otherwise
        """
        try:
            return self.loader.context.username
        except:
            return None
    
    def get_loader(self) -> instaloader.Instaloader:
        """
        Get the instaloader instance
        
        Returns:
            Instaloader instance
        """
        return self.loader


def create_env_file():
    """Create a .env file template for credentials"""
    env_content = """# Instagram Credentials
INSTAGRAM_USERNAME=your_username_here
INSTAGRAM_PASSWORD=your_password_here

# Optional: Rate limiting settings
REQUESTS_PER_MINUTE=60
DELAY_BETWEEN_REQUESTS=1
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"{Fore.GREEN}✓ Created .env file. Please add your credentials.")
    else:
        print(f"{Fore.YELLOW}.env file already exists.")


if __name__ == "__main__":
    # Test the authentication module
    auth = InstagramAuth()
    
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Example usage
    username = input("Enter Instagram username: ")
    password = input("Enter Instagram password: ")
    
    if auth.login(username, password):
        print(f"Successfully logged in as: {auth.get_username()}")
        auth.logout()
    else:
        print("Login failed.")
