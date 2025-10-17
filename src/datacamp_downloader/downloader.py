import os
from pathlib import Path
from typing import List, Optional

import typer

from . import active_session, datacamp
from .helper import Logger
from .templates.lang import Language

__version__ = "3.3.0"


def version_callback(value: bool):
    if value:
        typer.echo(f"Datacamp Downloader CLI Version: {__version__}")
        raise typer.Exit()


def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version.",
    ),
):
    pass


app = typer.Typer(callback=main)


@app.command()
def login(
    username: str = typer.Option(..., "-u", "--username", prompt=True),
    password: str = typer.Option(..., "-p", "--password", prompt=True, hide_input=True),
):
    """Log in to Datacamp using your username and password."""
    datacamp.login(username, password)


@app.command()
def set_token(token: str = typer.Argument(...)):
    """Log in to Datacamp using your token."""
    datacamp.set_token(token)


@app.command()
def tracks(
    refresh: Optional[bool] = typer.Option(
        False, "--refresh", "-r", is_flag=True, help="Refresh completed tracks."
    )
):
    """List your completed tracks."""
    datacamp.list_completed_tracks(refresh)


@app.command()
def courses(
    refresh: Optional[bool] = typer.Option(
        False, "--refresh", "-r", is_flag=True, help="Refresh completed courses."
    )
):
    """List your completed courses."""
    datacamp.list_completed_courses(refresh)


@app.command()
def ongoing(
    refresh: Optional[bool] = typer.Option(
        False, "--refresh", "-r", is_flag=True, help="Refresh enrolled courses."
    )
):
    """List your ongoing/enrolled courses (not yet completed)."""
    datacamp.list_enrolled_courses(refresh)


@app.command(name="skill-tracks")
def skill_tracks(
    filter: Optional[str] = typer.Option(
        "all",
        "--filter",
        "-f",
        help="Filter tracks: all, enrolled, active, completed, foundational, certification"
    )
):
    """List available DataCamp skill tracks.
    
    Skill tracks are curated learning paths focused on specific skills.
    
    Filters:
    - all: Show all available skill tracks (default)
    - enrolled: Show only enrolled tracks
    - active: Show only active tracks  
    - completed: Show only completed tracks
    - foundational: Show foundational tracks
    - certification: Show tracks with certification available
    
    Example: `datacamp skill-tracks --filter foundational`
    """
    datacamp.list_skill_tracks(filter)


@app.command()
def download(
    ids: List[str] = typer.Argument(
        ...,
        help="IDs for courses/tracks to download or `all` to download all your completed courses or `all-t` to download all your completed tracks.",
    ),
    path: Path = typer.Option(
        Path(os.getcwd() + "/Datacamp"),
        "--path",
        "-p",
        help="Path to the download directory.",
        dir_okay=True,
        file_okay=False,
    ),
    slides: Optional[bool] = typer.Option(
        True,
        "--slides/--no-slides",
        help="Download slides.",
    ),
    datasets: Optional[bool] = typer.Option(
        True,
        "--datasets/--no-datasets",
        help="Download datasets.",
    ),
    videos: Optional[bool] = typer.Option(
        True,
        "--videos/--no-videos",
        help="Download videos.",
    ),
    exercises: Optional[bool] = typer.Option(
        True,
        "--exercises/--no-exercises",
        help="Download exercises.",
    ),
    subtitles: Optional[List[Language]] = typer.Option(
        [Language.EN.value],
        "--subtitles",
        "-st",
        help="Choose subtitles to download.",
        case_sensitive=False,
    ),
    audios: Optional[bool] = typer.Option(
        False,
        "--audios/--no-audios",
        help="Download audio files.",
    ),
    scripts: Optional[bool] = typer.Option(
        True,
        "--scripts/--no-scripts",
        "--transcript/--no-transcript",
        show_default=True,
        help="Download scripts or transcripts.",
    ),
    python_file: Optional[bool] = typer.Option(
        True,
        "--python-file/--no-python-file",
        show_default=True,
        help="Download your own solution as a python file if available.",
    ),
    warnings: Optional[bool] = typer.Option(
        True,
        "--no-warnings",
        flag_value=False,
        is_flag=True,
        help="Disable warnings.",
    ),
    overwrite: Optional[bool] = typer.Option(
        False,
        "--overwrite",
        "-w",
        flag_value=True,
        is_flag=True,
        help="Overwrite files if exist.",
    ),
):
    """Download courses/tracks given their ids.

    Example: `datacamp download id1 id2 id3`\n
    To download all your completed courses run:
    \t`datacamp download all`\n
    To download all your completed tracks run:
    \t`datacamp download all-t`
    """
    Logger.show_warnings = warnings
    datacamp.download(
        ids,
        path,
        slides=slides,
        datasets=datasets,
        videos=videos,
        exercises=exercises,
        subtitles=subtitles,
        audios=audios,
        scripts=scripts,
        overwrite=overwrite,
        last_attempt=python_file,
    )


@app.command()
def download_skill_track(
    track_id: int = typer.Argument(
        ...,
        help="Skill Track ID to download (use 'skill-tracks' command to see available tracks).",
    ),
    path: Path = typer.Option(
        Path(os.getcwd() + "/Datacamp"),
        "--path",
        "-p",
        help="Path to the download directory.",
        dir_okay=True,
        file_okay=False,
    ),
    slides: Optional[bool] = typer.Option(
        True,
        "--slides/--no-slides",
        help="Download slides.",
    ),
    datasets: Optional[bool] = typer.Option(
        True,
        "--datasets/--no-datasets",
        help="Download datasets.",
    ),
    videos: Optional[bool] = typer.Option(
        True,
        "--videos/--no-videos",
        help="Download videos.",
    ),
    exercises: Optional[bool] = typer.Option(
        True,
        "--exercises/--no-exercises",
        help="Download exercises.",
    ),
    subtitles: Optional[List[Language]] = typer.Option(
        [Language.EN.value],
        "--subtitles",
        "-st",
        help="Choose subtitles to download (e.g., en, es, fr).",
        case_sensitive=False,
    ),
    audios: Optional[bool] = typer.Option(
        False,
        "--audios/--no-audios",
        help="Download audios.",
    ),
    scripts: Optional[bool] = typer.Option(
        True,
        "--scripts/--no-scripts",
        help="Download scripts.",
    ),
    python_file: Optional[bool] = typer.Option(
        False,
        "--python-file",
        "-py",
        help="Download exercises on last attempt as Python files instead of Markdown.",
    ),
    overwrite: Optional[bool] = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Overwrite existing files.",
    ),
):
    """
    Download all courses from a skill track.
    
    First, use 'skill-tracks' command to browse available tracks and get their IDs.
    Then use this command to download all courses in that track.
    
    Example:
        python cli.py skill-tracks --filter foundational
        python cli.py download-skill-track 44 --path ./MyDownloads
    """
    datacamp.download_skill_track(
        track_id,
        path,
        slides=slides,
        datasets=datasets,
        videos=videos,
        exercises=exercises,
        subtitles=subtitles,
        audios=audios,
        scripts=scripts,
        overwrite=overwrite,
        last_attempt=python_file,
    )


@app.command()
def reset():
    """Restart the session."""
    active_session.reset()


@app.command()
def download_ongoing(
    course_ids: List[int] = typer.Argument(
        ...,
        help="Course IDs to download (e.g., 14519 25475 33509).",
    ),
    path: Path = typer.Option(
        Path(os.getcwd() + "/Datacamp"),
        "--path",
        "-p",
        help="Path to the download directory.",
        dir_okay=True,
        file_okay=False,
    ),
    slides: Optional[bool] = typer.Option(
        True,
        "--slides/--no-slides",
        help="Download slides.",
    ),
    datasets: Optional[bool] = typer.Option(
        True,
        "--datasets/--no-datasets",
        help="Download datasets.",
    ),
    videos: Optional[bool] = typer.Option(
        True,
        "--videos/--no-videos",
        help="Download videos.",
    ),
    exercises: Optional[bool] = typer.Option(
        True,
        "--exercises/--no-exercises",
        help="Download exercises.",
    ),
    subtitles: Optional[List[Language]] = typer.Option(
        [Language.EN.value],
        "--subtitles",
        "-st",
        help="Choose subtitles to download.",
        case_sensitive=False,
    ),
    audios: Optional[bool] = typer.Option(
        False,
        "--audios/--no-audios",
        help="Download audio files.",
    ),
    scripts: Optional[bool] = typer.Option(
        True,
        "--scripts/--no-scripts",
        "--transcript/--no-transcript",
        show_default=True,
        help="Download scripts or transcripts.",
    ),
    overwrite: Optional[bool] = typer.Option(
        False,
        "--overwrite",
        "-w",
        flag_value=True,
        is_flag=True,
        help="Overwrite files if exist.",
    ),
):
    """Download ongoing/enrolled courses by their course IDs.
    
    This command downloads courses that are enrolled but not yet completed.
    Use course IDs from the 'ongoing' command.

    Example: `datacamp download-ongoing 14519 25475 33509`
    """
    import requests
    from .templates.course import Course
    
    # Get token from active session
    if not datacamp.token:
        Logger.error("Please login first using 'set-token' command!")
        return
    
    Logger.info(f"Fetching {len(course_ids)} ongoing course(s)...")
    
    headers = {
        "Authorization": f"Bearer {datacamp.token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Fetch and add each course to the download list
    courses_to_download = []
    
    for course_id in course_ids:
        Logger.info(f"Fetching course {course_id}...")
        
        try:
            response = requests.get(
                f"https://campus-api.datacamp.com/api/courses/{course_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                Logger.error(f"Failed to fetch course {course_id} (Status: {response.status_code})")
                continue
            
            course_data = response.json()
            
            # Create Course object
            course = Course(
                id=course_data['id'],
                title=course_data['title'],
                description=course_data.get('description', ''),
                slug=course_data.get('slug'),
                datasets=course_data.get('datasets', []),
                chapters=course_data.get('chapters', []),
                time_needed=f"{course_data.get('time_needed_in_hours', 2)} hours"
            )
            
            # Add to datacamp courses with order number
            course.order = len(datacamp.courses) + 1
            datacamp.courses.append(course)
            courses_to_download.append(course.order)
            
            Logger.info(f"✓ {course.title} (Order: {course.order})")
            
        except Exception as e:
            Logger.error(f"Error fetching course {course_id}: {e}")
            continue
    
    if not courses_to_download:
        Logger.error("No courses to download!")
        return
    
    # Download all fetched courses
    Logger.info(f"\nDownloading {len(courses_to_download)} course(s) to {path}...")
    
    datacamp.download(
        courses_to_download,
        path,
        slides=slides,
        datasets=datasets,
        videos=videos,
        exercises=exercises,
        subtitles=subtitles,
        audios=audios,
        scripts=scripts,
        overwrite=overwrite,
        last_attempt=False,  # No last attempt for ongoing courses
    )
