#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".opus",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Distribute songs evenly across automatically calculated "
            "directories while spreading songs by the same artist."
        )
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing the song files",
    )

    parser.add_argument(
        "--directories",
        type=int,
        help=(
            "Override the automatically calculated number of directories"
        ),
    )

    parser.add_argument(
        "--files-per-directory",
        type=int,
        help=(
            "Choose the directory count based on a preferred maximum "
            "number of songs per directory"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=("copy", "move"),
        default="copy",
        help="Copy or move files. Default: copy",
    )

    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed for reproducible results",
    )

    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Process all regular files, not only recognized audio files",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform the operation. Without this option, show the plan only.",
    )

    return parser.parse_args()


def get_artist(filename: str) -> str:
    """
    Extract the artist from filenames formatted as:

        Artist - Song title.mp3
    """

    stem = Path(filename).stem

    if " - " not in stem:
        return stem.strip().casefold()

    artist, _ = stem.split(" - ", 1)
    return artist.strip().casefold()


def calculate_directory_count(
    file_count: int,
    requested_directories: int | None,
    files_per_directory: int | None,
) -> tuple[int, str]:
    if requested_directories is not None:
        if requested_directories < 1:
            raise ValueError(
                "--directories must be a positive integer"
            )

        if requested_directories > file_count:
            raise ValueError(
                "--directories cannot exceed the number of files"
            )

        return requested_directories, "manual override"

    if files_per_directory is not None:
        if files_per_directory < 1:
            raise ValueError(
                "--files-per-directory must be a positive integer"
            )

        directory_count = math.ceil(
            file_count / files_per_directory
        )

        return directory_count, (
            f"maximum {files_per_directory} files per directory"
        )

    directory_count = max(1, round(math.sqrt(file_count)))

    return directory_count, "square-root balancing rule"


def calculate_capacities(
    file_count: int,
    directory_count: int,
) -> list[int]:
    """
    Return balanced directory capacities.

    Example:

        218 files across 15 directories

        8 directories contain 15 files
        7 directories contain 14 files
    """

    base, remainder = divmod(file_count, directory_count)

    capacities = [
        base + (1 if index < remainder else 0)
        for index in range(directory_count)
    ]

    random.shuffle(capacities)

    return capacities


def summarize_capacities(
    capacities: list[int],
) -> str:
    counts = Counter(capacities)

    parts = []

    for songs_per_directory in sorted(counts, reverse=True):
        directory_total = counts[songs_per_directory]

        parts.append(
            f"{directory_total} director"
            f"{'y' if directory_total == 1 else 'ies'} "
            f"with {songs_per_directory} "
            f"song{'s' if songs_per_directory != 1 else ''}"
        )

    return "\n".join(parts)


def distribute_files(
    files: list[Path],
    capacities: list[int],
) -> list[list[Path]]:
    grouped: dict[str, list[Path]] = defaultdict(list)

    for file in files:
        grouped[get_artist(file.name)].append(file)

    for artist_files in grouped.values():
        random.shuffle(artist_files)

    artist_groups = list(grouped.items())

    random.shuffle(artist_groups)

    # Artists with the most songs are hardest to distribute.
    artist_groups.sort(
        key=lambda item: len(item[1]),
        reverse=True,
    )

    directories: list[list[Path]] = [
        [] for _ in capacities
    ]

    artist_counts: list[Counter[str]] = [
        Counter() for _ in capacities
    ]

    for artist, artist_files in artist_groups:
        for file in artist_files:
            available = [
                index
                for index, capacity in enumerate(capacities)
                if len(directories[index]) < capacity
            ]

            if not available:
                raise RuntimeError(
                    "No output directory has available space"
                )

            random.shuffle(available)

            chosen = min(
                available,
                key=lambda index: (
                    artist_counts[index][artist],
                    len(directories[index]) / capacities[index],
                    len(directories[index]),
                ),
            )

            directories[chosen].append(file)
            artist_counts[chosen][artist] += 1

    return directories


def check_output_directories(
    parent: Path,
    directory_count: int,
) -> None:
    for number in range(1, directory_count + 1):
        output_directory = parent / f"{number:03d}"

        if not output_directory.exists():
            continue

        if not output_directory.is_dir():
            raise RuntimeError(
                f"Output path exists but is not a directory: "
                f"{output_directory}"
            )

        if any(output_directory.iterdir()):
            raise RuntimeError(
                f"Output directory is not empty: {output_directory}"
            )


def show_plan(
    directories: list[list[Path]],
) -> None:
    print()

    for index, files in enumerate(directories, start=1):
        artists = Counter(
            get_artist(file.name)
            for file in files
        )

        repeated_artists = {
            artist: count
            for artist, count in artists.items()
            if count > 1
        }

        print(
            f"{index:03d}: "
            f"{len(files)} songs, "
            f"{len(artists)} distinct artist names"
        )

        if repeated_artists:
            repeated = ", ".join(
                f"{artist}={count}"
                for artist, count in sorted(
                    repeated_artists.items(),
                    key=lambda item: (
                        -item[1],
                        item[0],
                    ),
                )
            )

            print(f"     repeated: {repeated}")


def prepare_output(
    parent: Path,
    directories: list[list[Path]],
    mode: str,
) -> None:
    operation = (
        shutil.copy2
        if mode == "copy"
        else shutil.move
    )

    created_directories: list[Path] = []

    try:
        for directory_number, files in enumerate(
            directories,
            start=1,
        ):
            output_directory = (
                parent / f"{directory_number:03d}"
            )

            output_directory.mkdir()
            created_directories.append(output_directory)

            # Random playback order inside each directory.
            random.shuffle(files)

            width = max(3, len(str(len(files))))

            for position, source in enumerate(
                files,
                start=1,
            ):
                destination_name = (
                    f"{position:0{width}d}-{source.name}"
                )

                destination = (
                    output_directory / destination_name
                )

                if destination.exists():
                    raise RuntimeError(
                        f"Destination already exists: "
                        f"{destination}"
                    )

                operation(source, destination)

    except Exception:
        if mode == "copy":
            for directory in reversed(created_directories):
                shutil.rmtree(directory, ignore_errors=True)

        raise


def find_input_files(
    source_directory: Path,
    all_files: bool,
) -> list[Path]:
    files = []

    for path in source_directory.iterdir():
        if not path.is_file():
            continue

        if all_files or path.suffix.casefold() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return files


def main() -> int:
    args = parse_arguments()

    source_directory = (
        args.directory.expanduser().resolve()
    )

    if not source_directory.is_dir():
        print(
            f"Error: directory does not exist: "
            f"{source_directory}",
            file=sys.stderr,
        )
        return 1

    if (
        args.directories is not None
        and args.files_per_directory is not None
    ):
        print(
            "Error: use either --directories or "
            "--files-per-directory, not both.",
            file=sys.stderr,
        )
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    files = find_input_files(
        source_directory,
        args.all_files,
    )

    if not files:
        print("No matching files found.")
        return 0

    directory_count, calculation_method = (
        calculate_directory_count(
            file_count=len(files),
            requested_directories=args.directories,
            files_per_directory=args.files_per_directory,
        )
    )

    capacities = calculate_capacities(
        file_count=len(files),
        directory_count=directory_count,
    )

    check_output_directories(
        source_directory,
        directory_count,
    )

    directories = distribute_files(
        files,
        capacities,
    )

    print(f"Source: {source_directory}")
    print(f"Files found: {len(files)}")
    print(f"Directories: {directory_count}")
    print(f"Calculation: {calculation_method}")
    print(f"Mode: {args.mode}")
    print()
    print("Distribution:")
    print(summarize_capacities(capacities))

    show_plan(directories)

    if not args.execute:
        print()
        print("Dry run only. No files were changed.")
        print("Add --execute to perform the operation.")
        return 0

    prepare_output(
        source_directory,
        directories,
        args.mode,
    )

    print()
    print(
        f"{args.mode.capitalize()}d {len(files)} files "
        f"into {directory_count} directories."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            "\nInterrupted.",
            file=sys.stderr,
        )
        raise SystemExit(130)
    except Exception as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
