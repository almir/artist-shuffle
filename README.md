# Artist Shuffle

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

* Python 3.9 or newer

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

Using the same seed and the same input files produces the same directory layout and playback order.

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

## Project Structure

```text
artist-shuffle/
├── artist-shuffle.py
├── README.md
├── LICENSE
└── .gitignore
```

## License

Free to use, modify, and distribute.
