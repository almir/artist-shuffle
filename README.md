# Artist Shuffle

[![CI](https://github.com/almir/artist-shuffle/actions/workflows/ci.yml/badge.svg)](https://github.com/almir/artist-shuffle/actions/workflows/ci.yml)

## Overview

Artist Shuffle distributes a music collection into multiple directories while trying to spread songs by the same artist as evenly as possible.

It was designed for devices, such as many car stereos, that do not support shuffle playback. Instead of relying on the player to shuffle songs, the script prepares the collection in advance by creating balanced directories and randomizing the playback order within each directory.

## Features

* Automatically counts the number of songs.
* Automatically calculates a balanced number of output directories.
* Evenly distributes songs across those directories.
* Attempts to spread songs from the same artist across different directories whenever possible.
* Randomizes playback order inside each directory.
* Renames songs with sequential numeric prefixes (`001-`, `002-`, etc.) to preserve the intended playback order.
* Supports both copying and moving files.
* Includes a dry-run mode that previews the operation without modifying any files.
* Safely handles filenames containing spaces, quotes, Unicode characters, and other special characters.

## Requirements

* Python 3.12 or newer

The script uses only the Python standard library.

## Expected Filename Format

The script extracts the artist name from filenames formatted like:

```text
Artist Name - Song Title.mp3
Another Artist - Another Song.flac
```

Everything before the first `" - "` is treated as the artist name.

## Basic Usage

Preview the operation without making any changes:

```bash
./artist-shuffle.py /path/to/music
```

Move the files into the generated directories:

```bash
./artist-shuffle.py /path/to/music \
    --mode move \
    --execute
```

Copy the files instead of moving them:

```bash
./artist-shuffle.py /path/to/music \
    --mode copy \
    --execute
```

## Automatic Directory Calculation

By default, the script counts the input files and calculates a balanced number of directories using the square-root rule.

For example:

```text
218 songs
```

becomes

```text
15 directories
```

distributed as:

```text
8 directories with 15 songs
7 directories with 14 songs
```

## Specify the Number of Directories

To create an exact number of directories:

```bash
./artist-shuffle.py \
    /path/to/music \
    --directories 20
```

## Specify the Maximum Songs per Directory

To request approximately a maximum number of songs per directory:

```bash
./artist-shuffle.py \
    /path/to/music \
    --files-per-directory 20
```

The script calculates the required number of directories automatically.

## Dry Run

Running the script without `--execute` performs a dry run.

Example:

```bash
./artist-shuffle.py /path/to/music
```

The script displays:

* Number of songs found
* Number of output directories
* Songs per directory
* Artist distribution
* Artists that appear more than once in the same directory

No files are modified.

## Reproducible Results

To generate the same shuffle again later, specify a random seed:

```bash
./artist-shuffle.py \
    /path/to/music \
    --seed 12345 \
    --execute
```

Using the same seed and the same input files produces the same directory layout and playback order. The input files are sorted before shuffling, so the result does not depend on the order in which the operating system happens to list them.

## Example Output

```text
Music/
├── 001/
│   ├── 001-Artist A - Song 01.mp3
│   ├── 002-Artist B - Song 07.mp3
│   ├── 003-Artist C - Song 02.mp3
│   └── ...
│
├── 002/
│   ├── 001-Artist D - Song 03.mp3
│   ├── 002-Artist A - Song 12.mp3
│   └── ...
│
└── 003/
    └── ...
```

The numeric prefixes determine the playback order within each directory.

## Command-Line Options

| Option                    | Description                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| `--execute`               | Perform the operation. Without this option, the script performs a dry run.                    |
| `--mode copy`             | Copy files into the generated directories.                                                    |
| `--mode move`             | Move files into the generated directories.                                                    |
| `--directories N`         | Create exactly `N` output directories.                                                        |
| `--files-per-directory N` | Calculate the number of directories from the requested maximum number of songs per directory. |
| `--seed N`                | Use a fixed random seed for reproducible results.                                             |
| `--all-files`             | Process all regular files instead of only recognized audio files.                             |
| `--version`               | Print the version and exit.                                                                   |
| `-h`, `--help`            | Show the full help message and exit.                                                          |

## Typical Workflow

1. Place all songs into a single directory.

2. Preview the planned distribution:

```bash
./artist-shuffle.py /path/to/music
```

3. Execute the operation:

```bash
./artist-shuffle.py \
    /path/to/music \
    --mode copy \
    --execute
```

4. Copy the generated directories to your storage device.

## Notes

* The script spreads artists as evenly as mathematically possible.
* If one artist has significantly more songs than the number of output directories, some directories will naturally contain multiple songs by that artist.
* Collaborations are treated as separate artist names unless additional normalization is implemented.
* In `copy` mode the operation is fully reversible: if it fails partway through, any directories it created are removed and your originals are left untouched.
* In `move` mode a failure partway through cannot be undone automatically. The script prints a warning listing that some files may already have been moved. Preview with a dry run first, and consider `copy` mode if in doubt.

## Development

Install the development dependencies (only needed to run the tests and tooling — the tool itself needs nothing beyond the standard library):

```bash
python -m pip install -r requirements.txt
```

Install the pre-commit hooks (run once after cloning). This enforces the same checks CI runs, on every commit and push:

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

Run the test suite:

```bash
pytest
```

Lint and check formatting:

```bash
ruff check .
ruff format --check .
```

All of these run automatically on every push and pull request via GitHub Actions across Python 3.12 and 3.13.

## Project Structure

```text
artist-shuffle/
├── artist-shuffle.py        # the tool (standard library only)
├── tests/                   # pytest test suite
├── .github/workflows/ci.yml # lint, format check + test on Python 3.12–3.13
├── .github/dependabot.yml   # weekly action + dependency updates
├── .pre-commit-config.yaml  # local hooks mirroring CI
├── .python-version          # pinned Python version for local tooling
├── pyproject.toml           # ruff and pytest configuration
├── requirements.txt         # development dependencies (tests + tooling)
├── README.md
├── LICENSE
└── .gitignore
```

## License

Free to use, modify, and distribute.
