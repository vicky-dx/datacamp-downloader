import tempfile

HOME_PAGE = "https://www.datacamp.com/"
LOGIN_URL = "https://www.datacamp.com/users/sign_in"
LOGIN_DETAILS_URL = "https://www.datacamp.com/api/users/signed_in"

SESSION_FILE = tempfile.gettempdir() + "/.datacamp.v3"

PROFILE_URL = "https://www.datacamp.com/profile/{slug}"
PROFILE_DATA_URL = "https://www.datacamp.com/api/public/users/{slug}"
COURSE_DETAILS_API = "https://campus-api.datacamp.com/api/courses/{id}/"
EXERCISE_DETAILS_API = "https://campus-api.datacamp.com/api/exercise/{id}"
VIDEO_DETAILS_API = "https://projector.datacamp.com/api/videos/{hash}"
PROGRESS_API = "https://campus-api.datacamp.com/api/courses/{course_id}/chapters/{chapter_id}/progress"

# Learn Hub API (for skill tracks and career paths)
SKILL_TRACKS_API = "https://learn-hub-api.datacamp.com/tracks/skill"
CAREER_TRACKS_API = "https://learn-hub-api.datacamp.com/tracks/career"

LANGMAP = {
    "en": "English",
    "zh": "Chinese simplified",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "ru": "Russian",
    "es": "Spanish",
}

# ========================================================================
# Download Configuration Constants
# ========================================================================

# Selenium wait timeouts
DEFAULT_WAIT_TIMEOUT = 15  # seconds
SHORT_WAIT_TIMEOUT = 10  # seconds
LONG_WAIT_TIMEOUT = 30  # seconds
CLOUDFLARE_INITIAL_WAIT = 5  # seconds

# Download settings
DEFAULT_DOWNLOAD_RETRY = 3
DOWNLOAD_CHUNK_SIZE = 8192  # bytes

# Path separators and naming
CHAPTER_PREFIX = "chapter"
EXERCISE_PREFIX = "ex"
VIDEO_PREFIX = "ch"
SUBEXERCISE_SUFFIX = "sub"

# File extensions
VIDEO_EXTENSION = ".mp4"
AUDIO_EXTENSION = ".mp3"
SCRIPT_EXTENSION = "_script.md"
SUBTITLE_EXTENSION = ".vtt"
MARKDOWN_EXTENSION = ".md"
PYTHON_EXTENSION = ".py"

# Download folder names
DATASETS_FOLDER = "datasets"
EXERCISES_FOLDER = "exercises"
VIDEOS_FOLDER = "videos"
AUDIOS_FOLDER = "audios"
SCRIPTS_FOLDER = "scripts"

# Progress display
PROGRESS_BAR_WIDTH = 50
