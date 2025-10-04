# Datacamp Downloader (Enhanced Fork)

[![GitHub license](https://img.shields.io/github/license/vicky-dx/datacamp-downloader)](https://github.com/vicky-dx/datacamp-downloader/blob/master/LICENSE)
[![Original Repo](https://img.shields.io/badge/original-TRoboto/datacamp--downloader-blue)](https://github.com/TRoboto/datacamp-downloader)

> **Enhanced Fork** - This is an improved version of the original [datacamp-downloader](https://github.com/TRoboto/datacamp-downloader) by TRoboto with critical bug fixes and new features for downloading **ongoing/in-progress courses**.

## Table of Contents

- [Datacamp Downloader (Enhanced Fork)](#datacamp-downloader-enhanced-fork)
  - [What's New in This Fork](#whats-new-in-this-fork)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Installation](#installation)
    - [From Source (Recommended)](#from-source-recommended)
    - [Autocompletion](#autocompletion)
  - [Documentation](#documentation)
  - [Getting Started](#getting-started)
    - [Login](#login)
    - [Download Completed Courses](#download-completed-courses)
    - [🆕 Download Ongoing Courses](#-download-ongoing-courses)
  - [User Privacy](#user-privacy)
  - [Disclaimer](#disclaimer)

## What's New in This Fork

This enhanced version includes several critical improvements over the original:

### 🐛 **Critical Bug Fixes**
- ✅ **Session Management Bug** - Fixed session reference being lost after save/load operations
- ✅ **Decorator Bug** - Fixed `animate_wait` decorator to properly accept keyword arguments
- ✅ **Escape Sequence Warning** - Fixed invalid escape sequence in progress animations
- ✅ **Exercise Download Bug** - Added proper None checking to prevent crashes when exercises are missing
- ✅ **Cloudflare Bypass** - Improved reliability with better wait logic

### 🎁 **New Features**
- ⭐ **Download Ongoing Courses** - Now you can download courses you haven't completed yet!
- ⭐ **List Enrolled Courses** - View all your in-progress courses with the `ongoing` command
- ⭐ **Direct API Access** - Bypass browser automation for faster ongoing course downloads
- ⭐ **Enhanced CLI** - New `download-ongoing` command with full option support

### 📚 **Better Documentation**
- Complete CLI usage guide
- Quick start reference
- Comprehensive project summary

**All improvements are fully backward compatible with the original tool!**

## Update

**Enhanced Fork - October 2025**

This fork includes critical bug fixes and new features for downloading ongoing/in-progress courses. See [What's New](#whats-new-in-this-fork) section above.

**Original Tool - V3.2**

The original Datacamp Downloader V3.2 uses Selenium for the backend. See original changelog for version [3.0](https://github.com/TRoboto/datacamp-downloader/pull/39), [3.1](https://github.com/TRoboto/datacamp-downloader/pull/42)
and [3.2](https://github.com/TRoboto/datacamp-downloader/pull/47).

## Description

Datacamp Downloader is a command-line interface tool developed in Python to help you download your contents on [Datacamp](https://datacamp.com) and keep them locally on your computer.

**This enhanced fork** adds the ability to download **ongoing/in-progress courses** that you haven't completed yet, along with critical bug fixes and improvements.

Datacamp Downloader helps you download all videos, slides, audios, exercises, transcripts, datasets and subtitles in organized folders.

The original design and development of this tool was inspired by [udacimak](https://github.com/udacimak/udacimak). This fork is based on [TRoboto's datacamp-downloader](https://github.com/TRoboto/datacamp-downloader).

**Datacampers!**

If you find this enhanced fork helpful, please support the developers by starring this repository!

## Installation

### From Source (Recommended)

You can clone this enhanced fork and install it with:

```bash
git clone https://github.com/vicky-dx/datacamp-downloader.git
cd datacamp-downloader
pip install -e .
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/vicky-dx/datacamp-downloader.git
```

### Autocompletion

To allow command autocompletion with `[TAB][TAB]`, run:

```
datacamp --install-completion [bash|zsh|fish|powershell|pwsh]
```

Then restart the terminal.

**Note:** autocompletion might not be supported by all operating systems.

## Documentation

The available commands with full documentation can be found in:
- [CLI Usage Guide](CLI_USAGE_GUIDE.md) - Complete command reference with examples
- [Quick Start Guide](QUICK_START.md) - Quick reference for all commands
- [Project Summary](PROJECT_SUMMARY.md) - Technical details of all improvements
- [Original Docs](https://github.com/TRoboto/datacamp-downloader/blob/master/docs.md) - Original documentation

## Getting Started

### Login

**Option 1: Using Datacamp Authentication Token (Recommended)**

To login using your Datacamp authentication token, run:

```bash
datacamp set-token [TOKEN]
```

Or using the CLI wrapper:

```bash
python cli.py set-token [TOKEN]
```

Datacamp authentication token can be found in Datacamp website browser _cookies_.
To get your Datacamp authentication, follow these steps:

**Firefox**

1. Visit [datacamp.com](https://datacamp.com) and log in.
2. Open the **Developer Tools** (press `Cmd + Opt + J` on MacOS or `F12` on Windows).
3. Go to **Storage tab**, then **Cookies** > `https://www.datacamp.com`
4. Find `_dct` key, its **Value** is the Datacamp authentication token.

**Chrome**

1. Visit [datacamp.com](https://datacamp.com) and log in.
2. Open the **Developer Tools** (press `Cmd + Opt + J` on MacOS or `F12` on Windows).
3. Go to **Application tab**, then **Storage** > **Cookies** > `https://www.datacamp.com`
4. Find `_dct` key, its **Value** is the Datacamp authentication token.

---

**Security Note**

Datacamp authentication token is a secret key and is unique to you. **You should not share it publicly**.

---

If you provided valid credentials, you should see the following:

```
Hi, YOUR_NAME
Active subscription found
```

> **Note:** Active subscription is not required to use this tool.

---

### Download Completed Courses

First, you should list your completed courses/track.

To list your completed **courses**, run:

```
datacamp courses
```

To list your completed **tracks**, run:

```
datacamp tracks
```

Similar output to this should appear with your completed courses/tracks:

```
+--------+------------------------------------------+------------+------------+------------+
| ID     | Title                                    | Datasets   | Exercises  | Videos     |
+--------+------------------------------------------+------------+------------+------------+
| 1      | Introduction to Python                   | 2          | 46         | 11         |
+--------+------------------------------------------+------------+------------+------------+
| 2      | Introduction to SQL                      | 1          | 40         | 1          |
+--------+------------------------------------------+------------+------------+------------+
| 3      | Intermediate Python                      | 3          | 69         | 18         |
+--------+------------------------------------------+------------+------------+------------+
| 4      | Introduction to Data Science in Python   | 0          | 31         | 13         |
+--------+------------------------------------------+------------+------------+------------+
| 5      | Data Science for Everyone                | 0          | 33         | 15         |
+--------+------------------------------------------+------------+------------+------------+
| 6      | Joining Data in SQL                      | 3          | 40         | 13         |
+--------+------------------------------------------+------------+------------+------------+
| 7      | Data Manipulation with pandas            | 4          | 41         | 15         |
+--------+------------------------------------------+------------+------------+------------+
| 8      | Supervised Learning with scikit-learn    | 7          | 37         | 17         |
+--------+------------------------------------------+------------+------------+------------+
| 9      | Machine Learning for Everyone            | 0          | 25         | 12         |
+--------+------------------------------------------+------------+------------+------------+
| 10     | Python Data Science Toolbox (Part 1)     | 1          | 34         | 12         |
+--------+------------------------------------------+------------+------------+------------+
```

Now, you can download any of the courses/tracks with:

```
datacamp download id1 id2 id3
```

For example to download the first and second course, run:

```
datacamp download 1 2
```

- To download all your completed courses, run:

```
datacamp download all
```

- To download all your completed tracks, run:

```
datacamp download all-t
```

This by default will download **videos**, **slides**, **datasets**, **exercises**, **english subtitles** and **transcripts** in organized folders in the **current directory**.

To customize this behavior see `datacamp download` command in the [CLI Usage Guide](CLI_USAGE_GUIDE.md).

---

### 🆕 Download Ongoing Courses

**NEW FEATURE** - This fork now supports downloading ongoing/in-progress courses!

First, list your enrolled (ongoing) courses:

```bash
datacamp ongoing
# or
python cli.py ongoing
```

You'll see something like:

```
+--------+------------------------------------------+------------+
| ID     | Title                                    | Progress   |
+--------+------------------------------------------+------------+
| 14519  | PostgreSQL Summary Stats and Window...   | 25%        |
+--------+------------------------------------------+------------+
| 25475  | Introduction to Cloud Computing          | 50%        |
+--------+------------------------------------------+------------+
| 33509  | Introduction to Snowflake SQL            | 10%        |
+--------+------------------------------------------+------------+
```

Now download any ongoing course by its **actual ID** (not order number):

```bash
datacamp download-ongoing 14519
# or
python cli.py download-ongoing 14519
```

**Download with custom options:**

```bash
# Custom download path
python cli.py download-ongoing 14519 --path "./PostgreSQL_Course"

# Skip videos (download only exercises and slides)
python cli.py download-ongoing 14519 --no-videos

# Skip exercises
python cli.py download-ongoing 14519 --no-exercises

# Download only videos
python cli.py download-ongoing 14519 --no-slides --no-datasets --no-exercises
```

**Download multiple ongoing courses:**

```bash
python cli.py download-ongoing 14519 25475 33509
```

The `download-ongoing` command supports all the same options as the regular `download` command:
- `--path` - Custom download directory
- `--no-videos` - Skip video downloads
- `--no-slides` - Skip slide downloads
- `--no-datasets` - Skip dataset downloads
- `--no-exercises` - Skip exercise downloads
- `--no-subtitles` - Skip subtitle downloads

See [CLI_USAGE_GUIDE.md](CLI_USAGE_GUIDE.md) for complete documentation.

---

## User Privacy

`datacamp` creates a session file with your credentials saved in the temp folder. If you no longer need to use the tool, it is preferable to reset the session, which will remove the saved file, with:

```
datacamp reset
```

## Disclaimer

This CLI is provided to help you download Datacamp courses/tracks for personal use only. Sharing the content of the courses is strictly prohibited under [Datacamp's Terms of Use](https://www.datacamp.com/terms-of-use/).

By using this CLI, the developers of this CLI are not responsible for any law infringement caused by the users of this CLI.

---

## Credits

- **Original Author**: [TRoboto](https://github.com/TRoboto) - [Original Repository](https://github.com/TRoboto/datacamp-downloader)
- **Enhanced Fork**: [vicky-dx](https://github.com/vicky-dx) - Added ongoing course support and critical bug fixes
- **Inspiration**: [udacimak](https://github.com/udacimak/udacimak)

---

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/vicky-dx/datacamp-downloader/issues).

## License

This project maintains the same license as the original repository. See [LICENSE](LICENSE) file for details.
