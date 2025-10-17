"""
DataCamp API interaction and course management utilities.

This module provides the core functionality for interacting with DataCamp's API,
including authentication, course/track listing, and content downloading.
"""

import re
import sys
import traceback
from functools import wraps
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import datacamp_downloader.session as session

from .constants import (
    AUDIOS_FOLDER,
    AUDIO_EXTENSION,
    CAREER_TRACKS_API,
    CHAPTER_PREFIX,
    COURSE_DETAILS_API,
    DATASETS_FOLDER,
    DEFAULT_WAIT_TIMEOUT,
    EXERCISE_DETAILS_API,
    EXERCISES_FOLDER,
    EXERCISE_PREFIX,
    LANGMAP,
    LOGIN_DETAILS_URL,
    LOGIN_URL,
    MARKDOWN_EXTENSION,
    PROFILE_DATA_URL,
    PROGRESS_API,
    PYTHON_EXTENSION,
    SCRIPTS_FOLDER,
    SCRIPT_EXTENSION,
    SHORT_WAIT_TIMEOUT,
    SKILL_TRACKS_API,
    SUBEXERCISE_SUFFIX,
    VIDEO_DETAILS_API,
    VIDEO_EXTENSION,
    VIDEO_PREFIX,
    VIDEOS_FOLDER,
)
from .helper import (
    Logger,
    animate_wait,
    correct_path,
    download_file,
    fix_track_link,
    format_course_metadata,
    get_table,
    print_progress,
    save_text,
)
from .templates.course import Chapter, Course
from .templates.exercise import Exercise
from .templates.track import Track
from .templates.video import Video


# ============================================================================
# Decorators
# ============================================================================

def login_required(func):
    """Decorator to ensure user is logged in before executing the function.
    
    Args:
        func: Function to decorate (must be a Datacamp instance method)
        
    Returns:
        Wrapped function that checks login status before execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if not isinstance(self, Datacamp):
            Logger.error(
                f"@login_required can only decorate Datacamp class methods."
            )
            return None
        
        if not self.loggedin:
            Logger.error("Please login first using 'set-token' or 'login' command!")
            return None
        
        return func(*args, **kwargs)
    
    return wrapper


def try_except_request(func):
    """Decorator to handle exceptions in API request methods gracefully.
    
    Args:
        func: Function to decorate (must be a Datacamp instance method)
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if not isinstance(self, Datacamp):
            Logger.error(
                f"@try_except_request can only decorate Datacamp class methods."
            )
            return None

        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if error_msg:
                Logger.error(f"Request failed: {error_msg}")
            # Log full traceback for debugging (optional)
            if Logger.show_warnings:
                traceback.print_exc()
        
        return None
    
    return wrapper


# ============================================================================
# Main Datacamp Class
# ============================================================================


class Datacamp:
    """Main class for interacting with DataCamp's platform.
    
    This class handles:
    - User authentication (username/password and token-based)
    - Course and track listing (completed and ongoing)
    - Content downloading (videos, slides, exercises, datasets)
    - API interactions with proper session management
    
    Attributes:
        session (Session): Browser session manager
        username (str): User's email/username
        password (str): User's password
        token (str): Authentication token (_dct cookie)
        has_active_subscription (bool): Whether user has active DataCamp subscription
        loggedin (bool): Authentication status
        login_data (dict): User profile data from login
        profile_data (dict): Extended user profile information
        courses (list[Course]): List of user's courses
        tracks (list[Track]): List of user's tracks
        not_found_courses (set): Set of course IDs that couldn't be fetched
    """
    
    def __init__(self, session: "session.Session") -> None:
        """Initialize Datacamp instance.
        
        Args:
            session: Session instance for browser automation and API calls
        """
        self.session = session
        self.init()

    def init(self):
        """Initialize/reset all instance variables to default state."""
        self.username = None
        self.password = None
        self.token = None
        self.has_active_subscription = False
        self.loggedin = False
        self.login_data = None
        self.profile_data = None

        self.courses = []
        self.tracks = []

        self.not_found_courses = set()

    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _save_debug_screenshot(self, filename: str) -> None:
        """Save a screenshot for debugging purposes.
        
        This is a DRY helper to eliminate duplicate screenshot saving code.
        Silently fails if screenshot cannot be saved.
        
        Args:
            filename: Name of the screenshot file (e.g., 'login_error.png')
        """
        try:
            self.session.driver.save_screenshot(filename)
        except Exception:
            # Silent fail - screenshot is for debugging only
            pass

    def _wait_for_element(self, by: By, value: str, timeout: int = DEFAULT_WAIT_TIMEOUT):
        """Wait for an element to become clickable and return it.
        
        Args:
            by: Selenium locator strategy (By.ID, By.XPATH, etc.)
            value: Locator value
            timeout: Maximum wait time in seconds (default: from constants)
            
        Returns:
            WebElement: The element when clickable
            
        Raises:
            TimeoutException: If element not found within timeout
        """
        return WebDriverWait(self.session.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def _find_and_click(self, by: By, value: str, error_msg: str, 
                        screenshot_name: str) -> bool:
        """Find an element and click it with error handling.
        
        Args:
            by: Selenium locator strategy
            value: Locator value
            error_msg: Error message to display on failure
            screenshot_name: Screenshot filename for debugging
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            element = self.session.driver.find_element(by, value)
            element.click()
            return True
        except Exception as e:
            Logger.error(f"{error_msg}: {e}")
            self._save_debug_screenshot(screenshot_name)
            return False

    def _fill_input_field(self, by: By, value: str, text: str, 
                          error_msg: str, screenshot_name: str) -> bool:
        """Fill an input field with robust error handling.
        
        Args:
            by: Selenium locator strategy
            value: Locator value
            text: Text to fill
            error_msg: Error message on failure
            screenshot_name: Screenshot filename for debugging
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            field = self._wait_for_element(by, value)
            field.clear()
            field.click()
            field.send_keys(text)
            return True
        except Exception as e:
            Logger.error(f"{error_msg}: {e}")
            self._save_debug_screenshot(screenshot_name)
            return False

    def _try_multiple_selectors(self, selectors: list) -> Optional[WebElement]:
        """Try multiple selectors and return first successful match.
        
        Args:
            selectors: List of (By, value) tuples to try
            
        Returns:
            WebElement or None: First element found, or None if all fail
        """
        for by, value in selectors:
            try:
                return self.session.driver.find_element(by, value)
            except Exception:
                continue
        return None

    # ========================================================================
    # Path Construction Helpers
    # ========================================================================
    
    def _build_course_path(self, base_path: Path, course: Course, 
                           index: str = "") -> Path:
        """Build the download path for a course.
        
        Args:
            base_path: Base directory for downloads
            course: Course object
            index: Optional index prefix (e.g., "1-")
            
        Returns:
            Path: Constructed course directory path
        """
        course_name = course.slug or course.title.lower().replace(" ", "-")
        return base_path / (index + correct_path(course_name))

    def _build_chapter_path(self, course_path: Path, chapter: Chapter) -> Path:
        """Build the download path for a chapter.
        
        Args:
            course_path: Course directory path
            chapter: Chapter object
            
        Returns:
            Path: Constructed chapter directory path
        """
        return course_path / self._get_chapter_name(chapter)

    def _build_video_path(self, chapter_path: Path, chapter_num: int, 
                          video_num: int) -> Path:
        """Build the base path for video-related files (no extension).
        
        Args:
            chapter_path: Chapter directory path
            chapter_num: Chapter number
            video_num: Video number within chapter
            
        Returns:
            Path: Base path for video files (e.g., "videos/ch1_2")
        """
        return chapter_path / VIDEOS_FOLDER / f"{VIDEO_PREFIX}{chapter_num}_{video_num}"

    def _build_exercise_path(self, chapter_path: Path, exercise_num: int) -> Path:
        """Build the path for an exercise file.
        
        Args:
            chapter_path: Chapter directory path
            exercise_num: Exercise number
            
        Returns:
            Path: Exercise file path
        """
        return chapter_path / EXERCISES_FOLDER / f"{EXERCISE_PREFIX}{exercise_num}{MARKDOWN_EXTENSION}"

    # ========================================================================
    # Download Helper Methods
    # ========================================================================
    
    def _download_datasets(self, course: Course, download_path: Path) -> None:
        """Download all datasets for a course.
        
        Args:
            course: Course object containing datasets
            download_path: Base path for course downloads
        """
        if not course.datasets:
            return
            
        for i, dataset in enumerate(course.datasets, 1):
            print_progress(i, len(course.datasets), "datasets")
            if dataset.asset_url:
                filename = dataset.asset_url.split("/")[-1]
                download_file(
                    dataset.asset_url,
                    download_path / DATASETS_FOLDER / correct_path(filename),
                    False,
                    overwrite=self.overwrite,
                )
        sys.stdout.write("\n")

    def _download_chapter_slides(self, chapter: Chapter, chapter_path: Path) -> None:
        """Download slides for a chapter.
        
        Args:
            chapter: Chapter object
            chapter_path: Path to chapter directory
        """
        if not chapter.slides_link:
            return
            
        filename = chapter.slides_link.split("/")[-1]
        download_file(
            chapter.slides_link,
            chapter_path / correct_path(filename),
            overwrite=self.overwrite,
        )

    def _process_video_downloads(self, video: Video, video_path: Path, 
                                  chapter_num: int, video_num: int, 
                                  chapter_path: Path, **kwargs) -> None:
        """Download video and related content (audio, subtitles, scripts).
        
        Args:
            video: Video object
            video_path: Base path for video files (without extension)
            chapter_num: Chapter number
            video_num: Video number
            chapter_path: Path to chapter directory
            **kwargs: Download options (videos, audios, subtitles, scripts)
        """
        videos = kwargs.get("videos")
        audios = kwargs.get("audios")
        scripts = kwargs.get("scripts")
        subtitles = kwargs.get("subtitles")
        
        # Download video file
        if videos and video.video_mp4_link:
            download_file(
                video.video_mp4_link,
                video_path.with_suffix(VIDEO_EXTENSION),
                overwrite=self.overwrite,
            )
        
        # Download audio file
        if audios and video.audio_link:
            audio_path = chapter_path / AUDIOS_FOLDER / f"{VIDEO_PREFIX}{chapter_num}_{video_num}{AUDIO_EXTENSION}"
            download_file(
                video.audio_link,
                audio_path,
                False,
                overwrite=self.overwrite,
            )
        
        # Download script
        if scripts and video.script_link:
            script_path = chapter_path / SCRIPTS_FOLDER / (video_path.name + SCRIPT_EXTENSION)
            download_file(
                video.script_link,
                script_path,
                False,
                overwrite=self.overwrite,
            )
        
        # Download subtitles
        if subtitles and video.subtitles:
            for sub_lang in subtitles:
                subtitle = self._get_subtitle(sub_lang, video)
                if not subtitle:
                    continue
                subtitle_path = video_path.parent / (video_path.name + f"_{sub_lang}.vtt")
                download_file(
                    subtitle.link,
                    subtitle_path,
                    False,
                    overwrite=self.overwrite,
                )

    def _process_exercise_content(self, exercise: Exercise, exercise_path: Path, 
                                   last_attempt: bool) -> None:
        """Process and save exercise content including subexercises.
        
        Args:
            exercise: Exercise object
            exercise_path: Path to save exercise file
            last_attempt: Whether to include last attempt code
        """
        # Save main exercise
        save_text(exercise_path, str(exercise), self.overwrite)
        
        # Save Python code if last attempt available
        if last_attempt and exercise.is_python and exercise.last_attempt:
            code_path = exercise_path.parent / (exercise_path.stem + PYTHON_EXTENSION)
            save_text(code_path, exercise.last_attempt, self.overwrite)
        
        # Process subexercises recursively
        subexs = exercise.data.subexercises
        if subexs:
            for i, subexercise in enumerate(subexs, 1):
                sub_exercise = self._get_exercise(subexercise)
                sub_path = exercise_path.parent / f"{exercise_path.stem}_{SUBEXERCISE_SUFFIX}{i}{MARKDOWN_EXTENSION}"
                self._process_exercise_content(sub_exercise, sub_path, last_attempt)

    # ========================================================================
    # Skill Tracks API Helpers
    # ========================================================================
    
    def _fetch_skill_tracks_data(self) -> Optional[dict]:
        """Fetch skill tracks data from DataCamp Learn Hub API.
        
        Centralizes API call logic to eliminate duplication across
        list_skill_tracks and download_skill_track methods.
        
        Returns:
            dict: API response with tracks data, or None if request fails
        """
        headers = {
            "accept": "*/*",
            "x-dc-lang": "en",
            "cookie": f"_dct={self.token}",
            "Referer": "https://app.datacamp.com/"
        }
        
        try:
            response = requests.get(SKILL_TRACKS_API, headers=headers, timeout=30)
            
            if response.status_code != 200:
                Logger.error(f"Failed to fetch skill tracks (Status: {response.status_code})")
                return None
            
            return response.json()
        except requests.exceptions.RequestException as e:
            Logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            Logger.error(f"Unexpected error fetching skill tracks: {e}")
            return None
    
    def _find_skill_track_by_id(self, track_id: int, tracks_data: dict) -> Optional[dict]:
        """Find a specific skill track by ID from API response.
        
        Args:
            track_id: Track ID to search for
            tracks_data: API response containing tracks list
            
        Returns:
            dict: Track data if found, None otherwise
        """
        all_tracks = tracks_data.get("tracks", [])
        
        for track in all_tracks:
            if track.get("id") == track_id:
                return track
        
        return None
    
    def _filter_skill_tracks(self, tracks: list, filter_type: str) -> list:
        """Filter skill tracks based on criteria.
        
        Implements separation of concerns by isolating filtering logic.
        
        Args:
            tracks: List of all skill tracks
            filter_type: Filter to apply (all/enrolled/active/completed/foundational/certification)
            
        Returns:
            list: Filtered tracks
        """
        if filter_type == "all":
            return tracks
        
        filtered = []
        for track in tracks:
            user_track = track.get("userTrack", {})
            
            if filter_type == "enrolled" and user_track.get("enrolled"):
                filtered.append(track)
            elif filter_type == "active" and user_track.get("active"):
                filtered.append(track)
            elif filter_type == "completed" and user_track.get("completionRate", 0) >= 100:
                filtered.append(track)
            elif filter_type == "foundational" and track.get("isFoundational"):
                filtered.append(track)
            elif filter_type == "certification" and track.get("certificationAvailable"):
                filtered.append(track)
        
        return filtered

    # ========================================================================
    # Authentication Methods
    # ========================================================================
    
    def _fill_email_field(self, username: str) -> bool:
        """Fill the email field in the login form.
        
        Args:
            username: User's email address
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self._fill_input_field(
            By.ID, "user_email", username,
            "Cannot find/fill email field",
            "login_error_email.png"
        )

    def _click_next_button(self) -> bool:
        """Click the next/continue button after email.
        
        Returns:
            bool: True if successful, False otherwise
        """
        selectors = [
            (By.XPATH, '//button[@tabindex="2"]'),
            (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        ]
        
        next_button = self._try_multiple_selectors(selectors)
        if next_button:
            try:
                next_button.click()
                return True
            except Exception as e:
                Logger.error(f"Cannot click next/continue button: {e}")
                self._save_debug_screenshot("login_error_next.png")
        else:
            Logger.error("Cannot find next/continue button")
            self._save_debug_screenshot("login_error_next.png")
        
        return False

    def _fill_password_field(self, password: str) -> bool:
        """Fill the password field with multiple fallback strategies.
        
        Tries: ActionChains -> direct send_keys -> JavaScript injection
        
        Args:
            password: User's password
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            password_field = self._wait_for_element(By.ID, "user_password")
        except Exception as e:
            Logger.error(
                f"Password field not found or not clickable (maybe SSO-only login?): {e}"
            )
            self._save_debug_screenshot("login_error_no_password.png")
            return False

        # Strategy 1: ActionChains
        try:
            ActionChains(self.session.driver).move_to_element(
                password_field
            ).click().send_keys(password).perform()
            return True
        except Exception:
            pass

        # Strategy 2: Direct send_keys
        try:
            password_field.clear()
            password_field.send_keys(password)
            return True
        except Exception:
            pass

        # Strategy 3: JavaScript injection
        try:
            self.session.driver.execute_script(
                "arguments[0].value = arguments[1]; "
                "arguments[0].dispatchEvent(new Event('input'));",
                password_field,
                password,
            )
            return True
        except Exception as e:
            Logger.error(f"Cannot type password into the field: {e}")
            self._save_debug_screenshot("login_error_password.png")
            return False

    def _submit_login_form(self, password_field) -> bool:
        """Submit the login form.
        
        Tries: Submit button -> Enter key
        
        Args:
            password_field: The password WebElement
            
        Returns:
            bool: True if submitted successfully
        """
        try:
            # Try to find and click the submit button
            submit_button = self.session.driver.find_element(
                By.XPATH, '//input[@tabindex="4"]'
            )
            submit_button.click()
        except Exception:
            # Fallback: Hit Enter on password field
            try:
                password_field.send_keys(Keys.RETURN)
            except Exception as e:
                Logger.error(f"Cannot submit login form: {e}")
                self._save_debug_screenshot("login_error_submit.png")
                return False
        
        return True

    def _extract_auth_token(self) -> bool:
        """Extract authentication token after successful login.
        
        Returns:
            bool: True if token extracted successfully
        """
        # Wait for page to load
        try:
            WebDriverWait(self.session.driver, 10).until(
                lambda d: "/users/sign_up" not in d.page_source
                and "Invalid" not in d.page_source
            )
        except Exception:
            pass  # Not fatal, proceed to check token

        # Extract token cookie
        try:
            token_cookie = self.session.driver.get_cookie("_dct")
            if not token_cookie:
                Logger.error(
                    "Login did not produce a _dct cookie "
                    "(likely login failed or SSO-only)."
                )
                self._save_debug_screenshot("login_no_token.png")
                return False
            
            self.token = token_cookie["value"]
            self._set_profile()
            return True
        except Exception as e:
            Logger.error(f"Error after login attempt: {e}")
            self._save_debug_screenshot("login_error_final.png")
            return False

    @animate_wait
    @try_except_request
    def login(self, username: str, password: str):
        """Log in to DataCamp using username and password.
        
        This method automates the browser-based login flow including:
        - Email entry
        - Next button click
        - Password entry (with multiple fallback strategies)
        - Form submission
        - Token extraction
        
        Args:
            username: User's email address
            password: User's password
        """
        # Quick guard
        if username == self.username and password == self.password and self.loggedin:
            Logger.info("Already logged in!")
            return

        self.init()
        self.username = username
        self.password = password

        # Open signin page
        req = self.session.get(LOGIN_URL)
        if not req:
            Logger.error("Cannot access DataCamp website!")
            return

        # Login flow
        if not self._fill_email_field(username):
            return

        Logger.info("Filled email")

        if not self._click_next_button():
            return

        if not self._fill_password_field(password):
            return

        Logger.info("Filled password")

        # Get password field for submission
        try:
            password_field = self.session.driver.find_element(By.ID, "user_password")
        except Exception:
            Logger.error("Password field lost after filling")
            return

        if not self._submit_login_form(password_field):
            return

        Logger.info("Submitted login form, waiting for result...")

        if self._extract_auth_token():
            Logger.info("Login flow completed successfully")

    # ========================================================================
    # Token Authentication
    # ========================================================================

    @animate_wait
    @try_except_request
    def set_token(self, token):
        """Authenticate using DataCamp authentication token.
        
        This is the recommended authentication method. The token can be found
        in browser cookies as '_dct' after logging into datacamp.com.
        
        Args:
            token (str): DataCamp authentication token (_dct cookie value)
        """
        if self.token == token and self.loggedin:
            Logger.info("Already logged in!")
            return

        # Reset state and clear cached data
        self.init()
        self.session.start()

        self.token = token
        self.session.add_token(token)
        self._set_profile()
        
        # Save session to persist the fresh state
        self.session.save()

    def get_profile_data(self, refresh: bool = False):
        """Fetch and cache extended user profile data from DataCamp API.
        
        Args:
            refresh (bool): If True, refetch data from API; if False, use cached data
        
        Returns:
            dict: User profile data including completed courses, tracks, etc.
        """
        if not self.profile_data or refresh:
            self.profile_data = self.session.get_json(
                PROFILE_DATA_URL.format(slug=self.login_data["slug"])
            )
            self.session.driver.minimize_window()
        return self.profile_data

    @login_required
    @animate_wait
    def list_completed_tracks(self, refresh):
        """Display a table of user's completed learning tracks.
        
        Args:
            refresh (bool): If True, refetch data from API; if False, use cached data
        """
        table = get_table()
        table.set_cols_width([6, 40, 10])
        table.add_row(["ID", "Title", "Courses"])
        table_so_far = table.draw()
        Logger.clear_and_print(table_so_far)
        for track in self.get_completed_tracks(refresh):
            table.add_row([track.id, track.title, len(track.courses)])
            table_str = table.draw()
            Logger.clear_and_print(table_str.replace(table_so_far, "").strip())
            table_so_far = table_str

    @login_required
    @animate_wait
    def list_completed_courses(self, refresh):
        """Display a table of user's completed courses.
        
        Args:
            refresh (bool): If True, refetch data from API; if False, use cached data
        """
        table = get_table()
        table.set_cols_width([6, 40, 10, 10, 10])
        table.add_row(["ID", "Title", "Datasets", "Exercises", "Videos"])
        table_so_far = table.draw()
        Logger.clear_and_print(table_so_far)
        for i, course in enumerate(self.get_completed_courses(refresh), 1):
            all_exercises_count = sum([c.nb_exercises for c in course.chapters])
            videos_count = sum([c.number_of_videos for c in course.chapters])
            course.order = i
            table.add_row(
                [
                    i,
                    course.title,
                    len(course.datasets),
                    all_exercises_count - videos_count,
                    videos_count,
                ]
            )
            table_str = table.draw()
            Logger.clear_and_print(table_str.replace(table_so_far, "").strip())
            table_so_far = table_str

    @login_required
    @animate_wait
    def list_enrolled_courses(self, refresh=False):
        """Display a table of user's ongoing/enrolled courses (not yet completed).
        
        These are courses that the user has started but not finished yet.
        Use the course IDs displayed here with the download-ongoing command.
        
        Args:
            refresh (bool): If True, refetch data from API; if False, use cached data
        """
        table = get_table()
        table.set_cols_width([6, 40, 10, 10, 10])
        table.add_row(["ID", "Title", "Duration", "XP", "Difficulty"])
        table_so_far = table.draw()
        Logger.clear_and_print(table_so_far)

        # Get profile data (with refresh support)
        profile = self.get_profile_data(refresh)
        enrolled_courses = profile.get("enrolled_courses", [])

        if not enrolled_courses:
            Logger.info("No ongoing courses found.")
            return

        for i, course_data in enumerate(enrolled_courses, 1):
            table.add_row(
                [
                    course_data.get("id", "N/A"),
                    course_data.get("title", "Unknown"),
                    f"{course_data.get('time_needed_in_hours', 'N/A')}h",
                    course_data.get("xp", "N/A"),
                    course_data.get("difficulty_level", "N/A"),
                ]
            )
            table_str = table.draw()
            Logger.clear_and_print(table_str.replace(table_so_far, "").strip())
            table_so_far = table_str

    @login_required
    @animate_wait
    def list_skill_tracks(self, filter_type: str = "all"):
        """Display a table of available DataCamp skill tracks.
        
        Skill tracks are curated learning paths focused on specific skills.
        They contain multiple courses and projects organized by skill level.
        
        Args:
            filter_type (str): Filter to apply:
                - "all": Show all available skill tracks
                - "enrolled": Show only enrolled tracks
                - "active": Show only active tracks
                - "completed": Show only completed tracks
                - "foundational": Show foundational tracks
                - "certification": Show tracks with certification
        """
        table = get_table()
        table.set_cols_width([6, 35, 8, 8, 12, 15])
        table.add_row(["ID", "Title", "Courses", "Time", "Tech", "Progress"])
        table_so_far = table.draw()
        Logger.clear_and_print(table_so_far)
        
        # Fetch skill tracks from Learn Hub API (DRY - using helper)
        data = self._fetch_skill_tracks_data()
        if not data:
            return
        
        all_tracks = data.get("tracks", [])
        if not all_tracks:
            Logger.info("No skill tracks found.")
            return
        
        # Filter tracks (SoC - separation of filtering logic)
        filtered_tracks = self._filter_skill_tracks(all_tracks, filter_type)
        
        if not filtered_tracks:
            Logger.info(f"No skill tracks found for filter: {filter_type}")
            return
        
        # Display tracks
        for track in filtered_tracks:
            user_track = track.get("userTrack", {})
            completion_rate = user_track.get("completionRate", 0)
            
            # Format technologies
            techs = track.get("technologies", [])
            tech_str = ", ".join(techs[:2])  # Show first 2 techs
            if len(techs) > 2:
                tech_str += f" +{len(techs)-2}"
            
            # Format progress
            if user_track.get("enrolled") or user_track.get("active"):
                progress_str = f"{completion_rate}%"
                if track.get("certificationAvailable"):
                    progress_str += " 🏆"
            else:
                progress_str = "Not enrolled"
                if track.get("certificationAvailable"):
                    progress_str = "🏆 Available"
            
            table.add_row([
                track.get("id", "N/A"),
                track.get("title", "Unknown")[:35],
                track.get("courseCount", "N/A"),
                track.get("timeNeeded", "N/A"),
                tech_str,
                progress_str
            ])
            
            table_str = table.draw()
            Logger.clear_and_print(table_str.replace(table_so_far, "").strip())
            table_so_far = table_str
        
        # Summary
        Logger.info(f"\nShowing {len(filtered_tracks)} skill track(s) | Filter: {filter_type}")

    @login_required
    def download_skill_track(self, track_id: int, path: Path, **kwargs):
        """Download all courses from a skill track.
        
        This method fetches the skill track details from the Learn Hub API,
        extracts all course IDs from the track, and downloads each course
        using the existing download infrastructure.
        
        Args:
            track_id (int): Skill track ID to download
            path (Path): Download directory path
            **kwargs: Download options (slides, datasets, videos, exercises, etc.)
        """
        # Fetch skill tracks data (DRY - using helper)
        Logger.info(f"Fetching skill track {track_id} details...")
        data = self._fetch_skill_tracks_data()
        if not data:
            return
        
        # Find the specific track (SoC - using helper)
        track = self._find_skill_track_by_id(track_id, data)
        
        if not track:
            Logger.error(f"Skill track with ID {track_id} not found!")
            Logger.info("Use 'skill-tracks' command to see available tracks")
            return
        
        # Extract track info
        track_title = track.get("title", "Unknown Track")
        course_ids = track.get("courseIds", [])
        
        if not course_ids:
            Logger.error(f"No courses found in track: {track_title}")
            return
        
        # Display track info
        Logger.info(f"\n{'='*80}")
        Logger.info(f"📚 Downloading Skill Track: {track_title}")
        Logger.info(f"📊 Total Courses: {len(course_ids)}")
        Logger.info(f"{'='*80}\n")
        
        # Download each course using existing infrastructure
        for i, course_id in enumerate(course_ids, 1):
            Logger.info(f"\n📥 [{i}/{len(course_ids)}] Downloading course {course_id}...")
            self.download([course_id], path, **kwargs)
        
        # Success message
        Logger.info(f"\n{'='*80}")
        Logger.info(f"✅ Successfully downloaded all {len(course_ids)} courses from: {track_title}")
        Logger.info(f"📁 Location: {path}")
        Logger.info(f"{'='*80}\n")

    @login_required
    def download(self, ids, directory, **kwargs):
        """Download courses or tracks with all their content.
        
        Supports downloading:
        - Individual courses by order number (e.g., 1, 2, 3)
        - Individual courses by course ID (e.g., 14519, 29303)
        - All completed courses with 'all'
        - Individual tracks with 't' prefix (e.g., 't1', 't2')
        - All completed tracks with 'all-t'
        
        Args:
            ids (list): List of course/track identifiers or special keywords
            directory (Path): Target directory for downloads
            **kwargs: Download options including:
                - slides (bool): Download slides (default: True)
                - videos (bool): Download videos (default: True)
                - datasets (bool): Download datasets (default: True)
                - exercises (bool): Download exercises (default: True)
                - subtitles (list): Subtitle languages to download (default: ['en'])
                - audios (bool): Download audio files (default: False)
                - scripts (bool): Download transcripts (default: True)
                - overwrite (bool): Overwrite existing files (default: False)
                - last_attempt (bool): Download user's solution code (default: True)
        
        Examples:
            download([1, 2], Path('./downloads'))  # Download first 2 courses
            download(['all'], Path('./downloads'))  # Download all completed
            download([14519], Path('./downloads'))  # Download by course ID
            download(['t1'], Path('./downloads'))  # Download track 1
        """
        self.overwrite = kwargs.get("overwrite")
        if "all-t" in ids:
            if not self.tracks:
                Logger.error(
                    "No tracks to download! Maybe run `datacamp tracks` first!"
                )
                return
            to_download = self.tracks
        elif "all" in ids:
            if not self.courses:
                Logger.error(
                    "No courses to download! Maybe run `datacamp courses` first!"
                )
                return
            to_download = self.courses
        else:
            to_download = []
            for id in ids:
                # Convert to string if it's an integer
                id_str = str(id)

                if "t" in id_str:
                    # It's a track ID (e.g., "t1", "t2")
                    track = self.get_track(id_str)
                    if not track:
                        Logger.warning(f"Track {id_str} is not fetched. Ignoring it.")
                        continue
                    to_download.append(track)
                elif id_str.isnumeric():
                    # It's a numeric ID - could be order number or actual course ID
                    course_num = int(id_str)

                    # First try as order number (1, 2, 3...)
                    course = self.get_course_by_order(course_num)

                    # If not found, try as actual course ID (14519, 29302, etc.)
                    if not course:
                        course = self.get_course(course_num)

                    if not course:
                        Logger.warning(f"Course {id_str} is not found. Ignoring it.")
                        continue
                    to_download.append(course)

        if not to_download:
            Logger.error("No courses/tracks to download!")
            return

        path = Path(directory) if not isinstance(directory, Path) else directory

        self.session.start()
        self.session.driver.minimize_window()

        for i, material in enumerate(to_download, 1):
            if not material:
                continue
            Logger.info(
                f"[{i}/{len(to_download)}] Start to download ({material.id}) {material.title}"
            )
            if isinstance(material, Course):
                self.download_course(material, path, **kwargs)
            else:
                self.download_track(material, path, **kwargs)

    def download_normal_exercise(
        self, exercise: Exercise, path: Path, include_last_attempt: bool = False
    ):
        """Download a normal exercise with optional last attempt code.
        
        DEPRECATED: Use _process_exercise_content instead.
        Kept for backward compatibility.
        
        Args:
            exercise: Exercise object
            path: Path to save exercise file
            include_last_attempt: Whether to include last attempt code
        """
        self._process_exercise_content(exercise, path, include_last_attempt)

    def download_track(self, track: Track, path: Path, **kwargs):
        """Download all courses in a track.
        
        Args:
            track: Track object containing courses
            path: Base download directory
            **kwargs: Download options (slides, videos, datasets, etc.)
        """
        track_path = path / correct_path(track.title)
        for i, course in enumerate(track.courses, 1):
            Logger.info(
                f"[{i}/{len(track.courses)}] Download ({course.id}) {course.title} from ({track.title} Track)"
            )
            self.download_course(course, track_path, f"{i}-", **kwargs)

    def download_course(self, course: Course, path: Path, index: str = "", **kwargs):
        """Download a complete course with all its content.
        
        Downloads datasets, slides, videos, exercises, audio, and scripts
        based on the options provided in kwargs.
        
        Args:
            course: Course object to download
            path: Base download directory
            index: Optional prefix for course folder (e.g., "1-")
            **kwargs: Download options including:
                - datasets (bool): Download datasets
                - slides (bool): Download slides
                - videos (bool): Download videos
                - exercises (bool): Download exercises
                - audios (bool): Download audio files
                - scripts (bool): Download transcripts
                - subtitles (list): Subtitle languages
                - last_attempt (bool): Include user's solution code
        """
        # Build course download path
        download_path = self._build_course_path(path, course, index)
        
        # Save course metadata as README.txt
        try:
            readme_path = download_path / "README.txt"
            metadata = format_course_metadata(course)
            save_text(readme_path, metadata, overwrite=self.overwrite)
        except Exception as e:
            Logger.warning(f"Failed to save course metadata: {e}")
        
        # Download datasets if requested
        if kwargs.get("datasets") and course.datasets:
            self._download_datasets(course, download_path)
        
        # Process each chapter
        for chapter in course.chapters:
            chapter_path = self._build_chapter_path(download_path, chapter)
            
            # Download chapter slides
            if kwargs.get("slides"):
                self._download_chapter_slides(chapter, chapter_path)
            
            # Download exercises, videos, and related content
            if any([
                kwargs.get("exercises"),
                kwargs.get("videos"),
                kwargs.get("audios"),
                kwargs.get("scripts")
            ]):
                self.download_others(course.id, chapter, chapter_path, **kwargs)

    def download_others(self, course_id: int, chapter: Chapter, path: Path, **kwargs):
        """Download exercises, videos, and related content for a chapter.
        
        This method processes all exercises/videos in a chapter sequentially,
        downloading the requested content types based on kwargs.
        
        Args:
            course_id: Course ID
            chapter: Chapter object
            path: Chapter download directory
            **kwargs: Download options (exercises, videos, audios, scripts, subtitles, last_attempt)
        """
        # Extract download options
        download_exercises = kwargs.get("exercises")
        download_last_attempt = kwargs.get("last_attempt")
        
        # Get exercise IDs and last attempts
        exercise_ids = self._get_exercises_ids(course_id, chapter.id)
        last_attempts = self.get_exercises_last_attempt(course_id, chapter.id)
        
        # Counters for naming
        exercise_counter = 1
        video_counter = 1
        
        # Process each exercise/video
        for i, exercise_id in enumerate(exercise_ids, 1):
            print_progress(i, len(exercise_ids), f"chapter {chapter.number}")
            
            exercise = self._get_exercise(exercise_id)
            if not exercise:
                continue
            
            # Attach last attempt if available
            exercise.last_attempt = last_attempts.get(exercise_id) if last_attempts else None
            
            # Handle regular exercises
            if download_exercises and not exercise.is_video:
                exercise_path = self._build_exercise_path(path, exercise_counter)
                self._process_exercise_content(exercise, exercise_path, download_last_attempt)
                exercise_counter += 1
            
            # Handle video exercises
            if exercise.is_video:
                video = self._get_video(exercise.data.get("projector_key"))
                if not video:
                    continue
                
                video_path = self._build_video_path(path, chapter.number, video_counter)
                self._process_video_downloads(
                    video, video_path, chapter.number, video_counter, path, **kwargs
                )
                video_counter += 1
            
            # Update progress
            print_progress(i, len(exercise_ids), f"chapter {chapter.number}")
        
        sys.stdout.write("\n")

    def get_completed_tracks(self, refresh=False):
        if self.tracks and not refresh:
            yield from self.tracks
            return

        self.tracks = []

        data = self.get_profile_data(refresh)
        completed_tracks = data["completed_tracks"]
        for i, track in enumerate(completed_tracks, 1):
            self.tracks.append(Track(f"t{i}", track["title"].strip(), track["url"]))
        all_courses = set()
        # add courses
        for track in self.tracks:
            courses = list(self._get_courses_from_link(fix_track_link(track.link)))
            if not courses:
                continue
            track.courses = courses
            all_courses.update(track.courses)
            yield track
        # add to courses
        current_ids = [c.id for c in self.courses]
        for course in all_courses:
            if course.id not in current_ids:
                self.courses.append(course)

        self.session.save()

    def get_completed_courses(self, refresh=False):
        if self.courses and not refresh:
            yield from self.courses
            return

        self.courses = []

        data = self.get_profile_data(refresh)
        completed_courses = data["completed_courses"]
        for course in completed_courses:
            fetched_course = self.get_course(course["id"])
            if not fetched_course:
                continue
            self.session.driver.minimize_window()
            self.courses.append(fetched_course)
            yield fetched_course

        if not self.courses:
            return []

        self.session.save()

    def get_course(self, id):
        if id in self.not_found_courses:
            return
        for course in self.courses:
            if course.id == id:
                return course
        return self._get_course(id)

    def get_course_by_order(self, order):
        for course in self.courses:
            if course.order == order and course.id not in self.not_found_courses:
                return course

    @try_except_request
    def get_exercises_last_attempt(self, course_id, chapter_id):
        data = self.session.get_json(
            PROGRESS_API.format(course_id=course_id, chapter_id=chapter_id)
        )
        if "error" in data:
            raise ValueError(
                f"Cannot get exercises for course {course_id}, chapter {chapter_id}."
            )
        last_attempt = {e["exercise_id"]: e["last_attempt"] for e in data}
        return last_attempt

    def get_track(self, id):
        for track in self.tracks:
            if track.id == id:
                return track

    @try_except_request
    def _get_courses_from_link(self, link: str):
        html = self.session.get(link)
        self.session.driver.minimize_window()

        soup = BeautifulSoup(html, "html.parser")
        courses_ids = soup.findAll("article", {"class": re.compile("^js-async")})
        for i, id_tag in enumerate(courses_ids, 1):
            id = id_tag.get("data-id")
            if not id:
                continue
            course = self.get_course(int(id))
            if course:
                yield course

    def _get_chapter_name(self, chapter: Chapter):
        if chapter.title and chapter.title_meta:
            return correct_path(chapter.slug)
        if chapter.title:
            return correct_path(
                f"chapter-{chapter.number}-{chapter.title.replace(' ', '-').lower()}"
            )
        return f"chapter-{chapter.number}"

    def _set_profile(self):
        try:
            data = self.session.get_json(LOGIN_DETAILS_URL)
        except Exception as e:
            Logger.error("Incorrect input token!")
            return

        Logger.info(
            "Hi, "
            + (data.get("first_name") or data.get("last_name") or data.get("email"))
        )

        # New API: 'has_active_subscription' may not exist anymore
        has_sub = False
        if "has_active_subscription" in data:
            has_sub = data["has_active_subscription"]
        elif "active_products" in data:
            has_sub = len(data["active_products"]) > 0

        if has_sub:
            Logger.info("Active subscription found")
        else:
            Logger.warning("No active subscription found")

        self.loggedin = True
        self.login_data = data
        self.has_active_subscription = has_sub

        self.session.save()

    def _get_subtitle(self, sub, video: Video):
        if not LANGMAP.get(sub):
            return
        for subtitle in video.subtitles:
            if subtitle.language == LANGMAP[sub]:
                return subtitle

    @try_except_request
    def _get_video(self, id):
        if not id:
            raise ValueError("ID tag not found.")
        res = self.session.get_json(VIDEO_DETAILS_API.format(hash=id))
        if "error" in res:
            raise ValueError()
        return Video(**res)

    @try_except_request
    def _get_exercises_ids(self, course_id, chapter_id):
        if not course_id or not chapter_id:
            raise ValueError("ID tags not found.")
        data = self.session.get_json(
            PROGRESS_API.format(course_id=course_id, chapter_id=chapter_id)
        )
        if "error" in data:
            raise ValueError(
                f"Cannot get exercises for course {course_id}, chapter {chapter_id}."
            )
        ids = [e["exercise_id"] for e in data]
        return ids

    @try_except_request
    def _get_exercise(self, id):
        if not id:
            raise ValueError("ID tag not found.")
        res = self.session.get_json(EXERCISE_DETAILS_API.format(id=id))
        if "error" in res:
            raise ValueError(f"Cannot get exercise with id: {id}.")
        return Exercise(**res)

    @try_except_request
    def _get_course(self, id):
        if not id:
            self.not_found_courses.add(id)
            raise ValueError("ID tag not found.")
        res = self.session.get_json(COURSE_DETAILS_API.format(id=id))
        if "error" in res:
            self.not_found_courses.add(id)
            raise ValueError()

        # Normalize time field
        time_needed = res.get("time_needed")
        if not time_needed and res.get("time_needed_in_hours") is not None:
            time_needed = f"{res['time_needed_in_hours']} hours"
        elif not time_needed and res.get("duration_minutes") is not None:
            hours = res["duration_minutes"] / 60
            time_needed = f"{hours:.1f} hours"

        return Course(
            id=res["id"],
            title=res["title"],
            description=res.get("description", ""),
            slug=res.get("slug"),
            datasets=res.get("datasets", []),
            chapters=res.get("chapters", []),
            time_needed=time_needed,
        )
