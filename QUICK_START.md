# Quick Reference - DataCamp Downloader

## Setup (One-time)
```bash
pip install -e .
```

## Login
```bash
python cli.py set-token "YOUR_DCT_TOKEN"
```

## List Courses
```bash
python cli.py courses          # Completed
python cli.py ongoing          # Ongoing (NEW!)
```

## Download
```bash
# Completed courses (by order number)
python cli.py download 1

# Ongoing courses (by course ID) - NEW!
python cli.py download-ongoing 14519
python cli.py download-ongoing 25475 --path "./MyFolder"
```

## All Commands
```bash
python cli.py --help

Commands:
  courses           List completed courses
  ongoing           List ongoing courses (NEW!)
  download          Download completed courses
  download-ongoing  Download ongoing courses (NEW!)
  set-token         Login with token
  login             Login with username/password
  tracks            List completed tracks
  reset             Reset session
```

## Your Ongoing Courses
- 14519 - PostgreSQL Summary Stats and Window Functions
- 25475 - Understanding Cloud Computing
- 29303 - Intermediate SQL  
- 33509 - Introduction to Snowflake SQL
- 39211 - Case Study: Data Analysis in Databricks

---
**Tip**: Use `download-ongoing` for courses you haven't completed yet!
