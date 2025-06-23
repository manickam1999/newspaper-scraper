#!/usr/bin/env python3
"""
Cookie Manager Utility Script

This script provides utilities to manage cookies for the Edge Weekly scraper.
Useful for testing, debugging, and manual cookie management.
"""

import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cookies import CookieManager
from utils.logger import logger
from src.scraper import setup_driver


def show_session_info():
    """Display current session information"""
    cookie_manager = CookieManager()
    info = cookie_manager.get_session_info()
    
    print("=== Session Information ===")
    print(f"Cookies exist: {info.get('cookies_exist', False)}")
    
    if info.get('cookies_exist'):
        print(f"Site: {info.get('site', 'Unknown')}")
        print(f"Saved at: {info.get('saved_at', 'Unknown')}")
        print(f"Expires at: {info.get('expires_at', 'Unknown')}")
        print(f"Is expired: {info.get('is_expired', 'Unknown')}")
        print(f"Cookie count: {info.get('cookie_count', 0)}")
    
    if info.get('session_state'):
        print("\nSession State:")
        for site, actions in info['session_state'].items():
            print(f"  {site}:")
            for action, timestamp in actions.items():
                print(f"    {action}: {timestamp}")
    
    if info.get('error'):
        print(f"Error: {info['error']}")


def clear_cookies():
    """Clear all saved cookies"""
    cookie_manager = CookieManager()
    if cookie_manager.clear_cookies():
        print("✅ Cookies cleared successfully")
    else:
        print("❌ Failed to clear cookies")


def test_authentication():
    """Test authentication with current cookies"""
    from utils.config import load_config
    
    try:
        config = load_config("config/config.yaml")
        edge_config = config["edge"]
        
        driver = setup_driver()
        cookie_manager = CookieManager()
        
        print("=== Testing Authentication ===")
        
        # Try to load and validate cookies
        driver.get(edge_config["url"])
        cookies_loaded = cookie_manager.load_cookies(driver, "edge")
        
        if cookies_loaded:
            print("✅ Cookies loaded successfully")
            if cookie_manager.are_cookies_valid(driver):
                print("✅ Cookies are valid - authentication successful")
            else:
                print("❌ Cookies are invalid - manual login required")
        else:
            print("❌ No cookies found - manual login required")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")


def force_login():
    """Force a fresh login and save new cookies"""
    from utils.config import load_config
    from src.scraper import login_and_save_cookies
    
    try:
        config = load_config("config/config.yaml")
        edge_config = config["edge"]
        
        driver = setup_driver()
        cookie_manager = CookieManager()
        
        print("=== Forcing Fresh Login ===")
        
        # Navigate to the site
        driver.get(edge_config["url"])
        
        # Perform fresh login
        success = login_and_save_cookies(
            driver, 
            cookie_manager, 
            edge_config["username"], 
            edge_config["password"]
        )
        
        if success:
            print("✅ Fresh login successful - cookies saved")
        else:
            print("❌ Fresh login failed")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Error during fresh login: {e}")


def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cookie Manager for Edge Weekly Scraper")
    parser.add_argument("action", choices=["info", "clear", "test", "login"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "info":
        show_session_info()
    elif args.action == "clear":
        clear_cookies()
    elif args.action == "test":
        test_authentication()
    elif args.action == "login":
        force_login()


if __name__ == "__main__":
    main()
