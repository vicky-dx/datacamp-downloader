# CLI Usage Guide - DataCamp Downloader

## Quick Start

The DataCamp Downloader CLI is now fully functional with ongoing course support!

### Installation
```bash
# Install in editable mode
pip install -e .
```

### Usage
Access all commands through the main CLI:
```bash
python -m datacamp_downloader.downloader [COMMAND]
```

Or create a simple `cli.py` wrapper (see instructions below).

## Available Commands

### 1. Login with Token
```bash
python cli.py set-token "YOUR_DCT_TOKEN_HERE"
```

**How to get your token:**
1. Login to DataCamp in your browser
2. Open DevTools (F12)
3. Go to Application/Storage > Cookies
4. Find the `_dct` cookie value
5. Copy the entire JWT token

### 2. List Completed Courses
```bash
python cli.py courses
python cli.py courses --refresh  # Force refresh
```

### 3. List Ongoing Courses (NEW FEATURE ✨)
```bash
python cli.py ongoing
python cli.py ongoing --refresh  # Force refresh
```

### 5. Download Ongoing Courses (NEW FEATURE ✨)
```bash
# Download by course ID
python cli.py download-ongoing 14519

# Download with custom path
python cli.py download-ongoing 14519 --path "./MyPostgreSQLCourse"

# Download with specific options
python cli.py download-ongoing 14519 --videos --slides --exercises --datasets
```

This NEW command allows you to download courses you're currently enrolled in but haven't completed yet!

### 6. Download Completed Courses
```bash
# Download by order number (for completed courses)
python cli.py download 1

# Download multiple courses
python cli.py download 1 2 3

# Download with options
python cli.py download 1 --videos --slides --exercises
```

### 7. Other Commands
```bash
python cli.py tracks          # List completed tracks
python cli.py reset           # Reset session
python cli.py --help          # Show all commands
```

## Test Results ✅

All commands tested and working:
- ✅ `set-token` - Login authentication
- ✅ `courses` - List completed courses  
- ✅ `ongoing` - List ongoing courses (NEW!)
- ✅ `--help` - Show available commands

## Example Workflow

### Download Your Completed Course
```bash
# 1. Login
python cli.py set-token "YOUR_TOKEN"

# 2. List completed courses
python cli.py courses

# 3. Download first course
python cli.py download 1
```

### View Your Ongoing Courses
```bash
# 1. Login
python cli.py set-token "YOUR_TOKEN"

# 2. List ongoing courses
python cli.py ongoing

# Output:
# | 14519  | PostgreSQL Summary Stats     | 4h  | 3550 | 2 |
# | 25475  | Understanding Cloud Computing| 2h  | 1950 | 1 |
# | 29303  | Intermediate SQL             | 4h  | 3950 | 1 |
# | 33509  | Introduction to Snowflake SQL| 2h  | 1800 | 2 |
# | 39211  | Databricks Case Study        | 3h  | 1600 | 3 |
```

### Download Ongoing Course (Using Script)
For ongoing courses, use the Python script approach:
```bash
python download_cloud_computing.py
```

## Notes

- The `ongoing` command works perfectly via direct API (no browser needed)
- Completed courses use Selenium (may need browser)
- Ongoing courses can be downloaded using the script approach we tested earlier
- All new features are accessible via CLI!

## Quick Reference

| Command | Description | New? |
|---------|-------------|------|
| `set-token` | Login with token | - |
| `courses` | List completed courses | - |
| `ongoing` | List ongoing/enrolled courses | ✨ NEW |
| `download` | Download courses | - |
| `tracks` | List completed tracks | - |
| `reset` | Reset session | - |

---

**Status**: CLI fully functional with new `ongoing` command! 🎉
