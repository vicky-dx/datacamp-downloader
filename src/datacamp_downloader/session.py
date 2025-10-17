import json
import os
import pickle
import time
from pathlib import Path

from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Prefer top-level undetected_chromedriver (works with Selenium 4); fallback to v2.
try:
    import undetected_chromedriver as uc
except Exception:
    import undetected_chromedriver.v2 as uc

# Selenium helper imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .constants import HOME_PAGE, SESSION_FILE
from .datacamp_utils import Datacamp


class Session:
    """Manages browser session and authentication for DataCamp API interactions.
    
    This class handles:
    - Chrome/Chromium browser automation via undetected-chromedriver
    - Cloudflare protection bypass
    - Cookie-based authentication
    - Session persistence via pickle
    - API request handling with proper authentication
    
    Attributes:
        savefile (Path): Path to the session pickle file
        datacamp (Datacamp): Associated Datacamp instance
        driver (WebDriver): Selenium WebDriver instance (created on demand)
    """
    
    def __init__(self) -> None:
        """Initialize a new Session instance and load saved state if available."""
        self.savefile = Path(SESSION_FILE)
        self.datacamp = self.load_datacamp()

    def save(self):
        """Save the current Datacamp state to disk.
        
        Note: The session reference is temporarily removed during pickling
        to avoid circular reference issues, then restored immediately.
        """
        # Temporarily set session to None for pickling
        temp_session = self.datacamp.session
        self.datacamp.session = None
        pickled = pickle.dumps(self.datacamp)
        self.savefile.write_bytes(pickled)
        # Restore the session reference
        self.datacamp.session = temp_session

    def load_datacamp(self):
        """Load saved Datacamp state from disk or create a new instance.
        
        Returns:
            Datacamp: Loaded or newly created Datacamp instance
        """
        if self.savefile.exists():
            datacamp = pickle.load(self.savefile.open("rb"))
            datacamp.session = self
            return datacamp
        return Datacamp(self)

    def reset(self):
        """Remove the saved session file, effectively logging out."""
        try:
            os.remove(SESSION_FILE)
        except:
            pass

    def _setup_driver(self, headless=True):
        """Configure and initialize the Chrome WebDriver.
        
        Args:
            headless (bool): Whether to run browser in headless mode. Default is True.
            
        Note:
            Creates a persistent Chrome profile in the package directory to
            maintain cookies and authentication across sessions.
        """
        # Try undetected_chromedriver options first, fallback to standard options
        try:
            options = uc.ChromeOptions()
        except Exception:
            options = ChromeOptions()

        # Configure headless mode
        try:
            options.headless = headless
        except Exception:
            if headless:
                options.add_argument("--headless=new")

        # Chrome arguments for stability and performance
        chrome_args = [
            "--no-first-run",
            "--no-service-autorun",
            "--password-store=basic",
            "--disable-extensions",
            "--disable-browser-side-navigation",
            "--disable-infobars",
            "--disable-popup-blocking",
            "--disable-gpu",
            "--disable-notifications",
            "--content-shell-hide-toolbar",
            "--top-controls-hide-threshold",
            "--force-app-mode",
            "--hide-scrollbars",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
        
        for arg in chrome_args:
            options.add_argument(arg)

        # Set up persistent Chrome profile for cookie/session persistence
        package_dir = os.path.dirname(os.path.abspath(__file__))
        profile_dir = os.path.join(package_dir, "dc_chrome_profile")
        os.makedirs(profile_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")

        # Initialize WebDriver
        service = ChromeService(executable_path=ChromeDriverManager().install())
        try:
            self.driver = uc.Chrome(service=service, options=options)
        except Exception:
            self.driver = webdriver.Chrome(service=service, options=options)

    def start(self, headless=False):
        """Initialize and start the browser session with proper authentication."""
        if hasattr(self, "driver"):
            return
        
        self._setup_driver(headless)
        
        # First visit homepage to establish domain context
        self.driver.get(HOME_PAGE)
        
        # Add authentication token before Cloudflare bypass for better success rate
        if self.datacamp.token:
            self.add_token(self.datacamp.token)
            # Refresh page to ensure cookie is properly set
            self.driver.refresh()
        
        # Bypass Cloudflare protection with token already in place
        self.bypass_cloudflare(HOME_PAGE)

    def bypass_cloudflare(self, url):
        """Wait for Cloudflare protection challenge to complete.
        
        Args:
            url: The URL being accessed (used for context, not for navigation)
        """
        import time

        try:
            # Initial wait for Cloudflare challenge to appear and potentially auto-complete
            time.sleep(5)

            # Cloudflare challenge indicators
            cloudflare_indicators = [
                "Just a moment",
                "cf-spinner",
                "Checking your browser",
                "Verifying you are human"
            ]

            # Wait for challenge to complete (max 30 seconds)
            max_attempts = 30
            attempts = 0
            
            while attempts < max_attempts:
                page_source = self.driver.page_source
                if any(indicator in page_source for indicator in cloudflare_indicators):
                    time.sleep(1)
                    attempts += 1
                else:
                    # Challenge completed
                    if attempts > 0:
                        # Extra wait after challenge completes for stability
                        time.sleep(2)
                    break

        except Exception:
            # Silent fail - continue with operation even if bypass detection fails
            pass

    def get(self, url):
        """Fetch a URL and return its page source after bypassing Cloudflare.
        
        Args:
            url: The URL to fetch
            
        Returns:
            str: The page source HTML
        """
        self.start()
        self.driver.get(url)
        self.bypass_cloudflare(url)
        return self.driver.page_source

    def get_json(self, url):
        """Fetch a URL and parse its JSON content.
        
        Some DataCamp API endpoints return JSON wrapped in <pre> tags,
        while others return raw JSON. This method handles both cases.
        
        Args:
            url: The URL to fetch
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            json.JSONDecodeError: If the response is not valid JSON
        """
        page = self.get(url).strip()

        # Parse with BeautifulSoup to extract JSON from <pre> tags if present
        soup = BeautifulSoup(page, "html.parser")
        pre_tag = soup.find("pre")

        if pre_tag:
            # JSON is wrapped in <pre> tags - extract the text content
            json_content = pre_tag.text
        else:
            # Raw JSON or full HTML page
            json_content = page

        return json.loads(json_content)

    def to_json(self, page: str):
        """Parse a JSON string.
        
        Args:
            page: JSON string to parse
            
        Returns:
            dict: Parsed JSON data
        """
        return json.loads(page)

    def get_element_by_id(self, id: str) -> WebElement:
        """Find and return a web element by its ID.
        
        Args:
            id: The element ID to search for
            
        Returns:
            WebElement: The found element
        """
        return self.driver.find_element(By.ID, id)

    def get_element_by_xpath(self, xpath: str) -> WebElement:
        """Find and return a web element by XPath.
        
        Args:
            xpath: The XPath expression
            
        Returns:
            WebElement: The found element
        """
        return self.driver.find_element(By.XPATH, xpath)

    def click_element(self, id: str):
        """Find an element by ID and click it.
        
        Args:
            id: The element ID to click
        """
        self.get_element_by_id(id).click()

    def wait_for_element_by_css_selector(self, *css: str, timeout: int = 10):
        """Wait for any of the specified CSS selectors to become visible.
        
        Args:
            *css: One or more CSS selectors to wait for
            timeout: Maximum wait time in seconds (default: 10)
        """
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_any_elements_located((By.CSS_SELECTOR, ",".join(css)))
        )

    def add_token(self, token: str):
        """Add DataCamp authentication token as a cookie.
        
        Args:
            token: The DataCamp authentication token (_dct cookie value)
        """
        cookie = {
            "name": "_dct",
            "value": token,
            "domain": ".datacamp.com",
            "secure": True,
        }
        self.driver.add_cookie(cookie)
        return self
