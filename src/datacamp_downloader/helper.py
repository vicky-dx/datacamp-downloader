import itertools
import re
import sys
import threading
import time
from pathlib import Path

import requests
from termcolor import colored
from texttable import Texttable


class Logger:
    show_warnings = True
    is_writing = False

    @classmethod
    def error(cls, text):
        Logger.print(text, "ERROR:", "red")

    @classmethod
    def clear(cls):
        sys.stdout.write("\r" + " " * 100 + "\r")

    @classmethod
    def warning(cls, text):
        if cls.show_warnings:
            Logger.print(text, "WARNING:", "yellow")

    @classmethod
    def info(cls, text):
        Logger.print(text, "INFO:", "green")

    @classmethod
    def print(cls, text, head, color=None, background=None, end="\n"):
        cls.is_writing = True
        Logger.clear()
        print(colored(f"{head}", color, background), text, end=end, flush=True)
        cls.is_writing = False

    @classmethod
    def clear_and_print(cls, text):
        cls.is_writing = True
        Logger.clear()
        print(text, flush=True)
        cls.is_writing = False


def get_table():
    table = Texttable()
    return table


def animate_wait(f):
    done = False

    def animate():
        for c in itertools.cycle(list("/—\\|")):
            if done:
                Logger.clear()
                break
            if not Logger.is_writing:
                print("\rPlease wait " + c, end="", flush=True)
            time.sleep(0.1)

    def wrapper(*args, **kwargs):
        nonlocal done
        done = False
        t = threading.Thread(target=animate)
        t.daemon = True
        t.start()
        output = f(*args, **kwargs)
        done = True
        return output

    return wrapper


def correct_path(path: str):
    return re.sub("[^-a-zA-Z0-9_.() /]+", "", path)


def download_file(link: str, path: Path, progress=True, max_retry=10, overwrite=False):
    # start = time.clock()
    if not overwrite and path.exists():
        Logger.warning(f"{path.absolute()} is already downloaded")
        return

    for i in range(max_retry):
        try:
            response = requests.get(link, stream=True)
            i = -1
            break
        except Exception:
            Logger.print(f"", f"Retry [{i+1}/{max_retry}]", "magenta", end="")

    if i != -1:
        Logger.error(f"Failed to download {link}")
        return

    path.parent.mkdir(exist_ok=True, parents=True)
    total_length = response.headers.get("content-length")

    with path.open("wb") as f:
        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=1024 * 1024):  # 1MB
                dl += len(data)
                f.write(data)
                if progress:
                    print_progress(dl, total_length, path.name)
    if progress:
        sys.stdout.write("\n")


def print_progress(progress, total, name, max=50):
    done = int(max * progress / total)
    Logger.print(
        "[%s%s] %d%%" % ("=" * done, " " * (max - done), done * 2),
        f"Downloading [{name}]",
        "blue",
        end="\r",
    )
    sys.stdout.flush()


def save_text(path: Path, content: str, overwrite=False):
    if not path.is_file:
        Logger.error(f"{path.absolute()} isn't a file")
        return
    if not overwrite and path.exists():
        Logger.warning(f"{path.absolute()} is already downloaded")
        return
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(content, encoding="utf8")
    # Logger.info(f"{path.name} has been saved.")


def fix_track_link(link):
    if "?" in link:
        link += "&embedded=true"
    else:
        link += "?embedded=true"
    return link


# ============================================================================
# Course JSON Helper Functions
# ============================================================================

def get_course_summary(course):
    """Extract summary information from Course object.
    
    Args:
        course: Course object with JSON data
        
    Returns:
        dict: Summary with id, title, chapters count, exercises count, duration
    """
    total_exercises = sum(chapter.nb_exercises for chapter in course.chapters)
    total_videos = sum(chapter.number_of_videos for chapter in course.chapters)
    
    return {
        "id": course.id,
        "title": course.title,
        "slug": course.slug,
        "chapters": len(course.chapters),
        "exercises": total_exercises,
        "videos": total_videos,
        "duration": course.time_needed,
        "difficulty": getattr(course, 'difficulty_level', 'N/A'),
        "language": getattr(course, 'programming_language', 'unknown'),
    }


def get_course_instructors(course):
    """Extract instructor names from Course object.
    
    Args:
        course: Course object with instructors
        
    Returns:
        list: List of instructor full names
    """
    return [instructor.full_name for instructor in course.instructors]


def get_course_datasets(course):
    """Extract dataset information from Course object.
    
    Args:
        course: Course object with datasets
        
    Returns:
        list: List of dicts with dataset name and URL
    """
    return [
        {"name": dataset.name, "url": dataset.asset_url}
        for dataset in course.datasets
    ]


def get_chapter_summary(chapter):
    """Extract summary information from Chapter object.
    
    Args:
        chapter: Chapter object
        
    Returns:
        dict: Summary with number, title, exercises, videos, XP
    """
    return {
        "number": chapter.number,
        "title": chapter.title,
        "exercises": chapter.nb_exercises,
        "videos": chapter.number_of_videos,
        "xp": chapter.xp,
        "slides_available": bool(chapter.slides_link),
    }


def get_course_chapters_info(course):
    """Get detailed info about all chapters in a course.
    
    Args:
        course: Course object
        
    Returns:
        list: List of chapter summaries
    """
    return [get_chapter_summary(chapter) for chapter in course.chapters]


def get_course_total_xp(course):
    """Calculate total XP available in a course.
    
    Args:
        course: Course object
        
    Returns:
        int: Total XP from all chapters
    """
    return sum(chapter.xp for chapter in course.chapters)


def get_video_exercises(chapter):
    """Extract only video exercises from a chapter.
    
    Args:
        chapter: Chapter object
        
    Returns:
        list: List of video Exercise objects
    """
    from .templates.course import TypeEnum
    return [
        ex for ex in chapter.exercises 
        if ex.type == TypeEnum.VIDEO_EXERCISE
    ]


def get_practice_exercises(chapter):
    """Extract only practice (non-video) exercises from a chapter.
    
    Args:
        chapter: Chapter object
        
    Returns:
        list: List of practice Exercise objects (Normal + MultipleChoice)
    """
    from .templates.course import TypeEnum
    return [
        ex for ex in chapter.exercises 
        if ex.type in [TypeEnum.NORMAL_EXERCISE, TypeEnum.MULTIPLE_CHOICE_EXERCISE]
    ]


def format_course_metadata(course):
    """Format course metadata for display or saving.
    
    Args:
        course: Course object
        
    Returns:
        str: Formatted metadata string
    """
    lines = [
        f"Course: {course.title}",
        f"ID: {course.id}",
        f"Slug: {course.slug}",
        f"Duration: {course.time_needed}",
        f"Difficulty: {getattr(course, 'difficulty_level', 'N/A')}",
        f"Language: {getattr(course, 'programming_language', 'unknown')}",
        f"Chapters: {len(course.chapters)}",
        f"Total XP: {get_course_total_xp(course)}",
        "",
        "Instructors:",
    ]
    
    for instructor in get_course_instructors(course):
        lines.append(f"  - {instructor}")
    
    if course.datasets:
        lines.append("")
        lines.append("Datasets:")
        for dataset in get_course_datasets(course):
            lines.append(f"  - {dataset['name']}")
    
    lines.append("")
    lines.append("Chapters Overview:")
    for ch_info in get_course_chapters_info(course):
        lines.append(
            f"  {ch_info['number']}. {ch_info['title']} "
            f"({ch_info['exercises']} exercises, {ch_info['videos']} videos, {ch_info['xp']} XP)"
        )
    
    return "\n".join(lines)
