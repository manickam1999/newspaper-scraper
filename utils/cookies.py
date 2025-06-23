import json
import os
from datetime import datetime, timedelta
from utils.logger import logger

class CookieManager:
    def __init__(self, session_dir="session"):
        self.session_dir = session_dir
        self.cookies_file = os.path.join(session_dir, "edge_cookies.json")
        self.session_state_file = os.path.join(session_dir, "session_state.json")
        
        # Create session directory if it doesn't exist
        os.makedirs(session_dir, exist_ok=True)
    
    def save_cookies(self, driver, site="edge"):
        """Extract and save cookies from Selenium driver"""
        try:
            cookies = driver.get_cookies()
            session_data = {
                "site": site,
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()  # Assume 7-day expiry
            }
            
            with open(self.cookies_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
            
            # Update session state
            self._update_session_state(site, "login_success")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self, driver, site="edge"):
        """Load and apply cookies to Selenium driver"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.info("No saved cookies found")
                return False
                
            with open(self.cookies_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if cookies are for the correct site
            if session_data.get("site") != site:
                logger.warning(f"Cookies are for {session_data.get('site')}, not {site}")
                return False
            
            # Check if cookies are expired
            if self._are_cookies_expired(session_data):
                logger.info("Saved cookies have expired")
                return False
            
            # Apply cookies to driver
            cookies = session_data.get("cookies", [])
            for cookie in cookies:
                try:
                    # Remove problematic keys that Selenium doesn't accept
                    clean_cookie = {k: v for k, v in cookie.items() 
                                  if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']}
                    driver.add_cookie(clean_cookie)
                except Exception as e:
                    logger.warning(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
            
            logger.info(f"Loaded {len(cookies)} cookies successfully")
            self._update_session_state(site, "cookies_loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def are_cookies_valid(self, driver, validation_selector="i.ti-user.ti-user-logged"):
        """Check if current cookies are still valid by looking for logged-in indicator"""
        try:
            # Refresh the page to test cookies
            driver.refresh()
            
            # Wait a bit for the page to load
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import TimeoutException
            
            # Check for logged-in indicator
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, validation_selector))
                )
                logger.info("Cookies are valid - user is logged in")
                return True
            except TimeoutException:
                logger.info("Cookies appear to be invalid - login indicator not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate cookies: {e}")
            return False
    
    def clear_cookies(self):
        """Clear saved cookies and session state"""
        try:
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.info("Cleared saved cookies")
            
            if os.path.exists(self.session_state_file):
                os.remove(self.session_state_file)
                logger.info("Cleared session state")
                
            return True
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            return False
    
    def _are_cookies_expired(self, session_data):
        """Check if cookies have expired"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            return datetime.now() > expires_at
        except Exception:
            # If we can't parse the expiry date, assume expired
            return True
    
    def _update_session_state(self, site, action):
        """Update session state tracking"""
        try:
            state = {}
            if os.path.exists(self.session_state_file):
                with open(self.session_state_file, 'r') as f:
                    state = json.load(f)
            
            if site not in state:
                state[site] = {}
            
            state[site][action] = datetime.now().isoformat()
            
            with open(self.session_state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update session state: {e}")
    
    def get_session_info(self):
        """Get information about current session state"""
        try:
            info = {"cookies_exist": os.path.exists(self.cookies_file)}
            
            if info["cookies_exist"]:
                with open(self.cookies_file, 'r') as f:
                    session_data = json.load(f)
                info.update({
                    "site": session_data.get("site"),
                    "saved_at": session_data.get("saved_at"),
                    "expires_at": session_data.get("expires_at"),
                    "is_expired": self._are_cookies_expired(session_data),
                    "cookie_count": len(session_data.get("cookies", []))
                })
            
            if os.path.exists(self.session_state_file):
                with open(self.session_state_file, 'r') as f:
                    info["session_state"] = json.load(f)
            
            return info
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {"error": str(e)}
