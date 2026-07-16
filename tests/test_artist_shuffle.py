"""Tests for artist-shuffle."""

from __future__ import annotations

import random
from collections import Counter

import pytest

# ---------------------------------------------------------------------------
# get_artist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("Adele - Hello.mp3", "adele"),
        ("Simon & Garfunkel - The Boxer.flac", "simon & garfunkel"),
        ("  Björk  - Jóga.opus", "björk"),
        ("ADELE - Someone Like You.mp3", "adele"),  # case folded
        ("NoSeparator.mp3", "noseparator"),  # whole stem is the artist
        ("Artist - Song - With - Dashes.mp3", "artist"),  # split once
    ],
)
def test_get_artist(artist_shuffle, filename, expected):
    assert artist_shuffle.get_artist(filename) == expected


# ---------------------------------------------------------------------------
# calculate_directory_count
# ---------------------------------------------------------------------------


def test_directory_count_square_root_rule(artist_shuffle):
    count, method = artist_shuffle.calculate_directory_count(218, None, None)
    assert count == 15  # round(sqrt(218)) == 15
    assert "square-root" in method


def test_directory_count_manual_override(artist_shuffle):
    count, method = artist_shuffle.calculate_directory_count(100, 20, None)
    assert count == 20
    assert method == "manual override"


def test_directory_count_files_per_directory_rounds_up(artist_shuffle):
    count, _ = artist_shuffle.calculate_directory_count(101, None, 20)
    assert count == 6  # ceil(101 / 20)


def test_directory_count_at_least_one(artist_shuffle):
    count, _ = artist_shuffle.calculate_directory_count(1, None, None)
    assert count == 1


@pytest.mark.parametrize(
    ("requested", "per_dir"),
    [(0, None), (-1, None), (None, 0), (None, -5)],
)
def test_directory_count_rejects_non_positive(artist_shuffle, requested, per_dir):
    with pytest.raises(ValueError):
        artist_shuffle.calculate_directory_count(10, requested, per_dir)


def test_directory_count_rejects_more_dirs_than_files(artist_shuffle):
    with pytest.raises(ValueError):
        artist_shuffle.calculate_directory_count(5, 10, None)


# ---------------------------------------------------------------------------
# calculate_capacities
# ---------------------------------------------------------------------------


def test_capacities_sum_to_file_count(artist_shuffle):
    capacities = artist_shuffle.calculate_capacities(218, 15)
    assert sum(capacities) == 218
    assert len(capacities) == 15


def test_capacities_are_balanced(artist_shuffle):
    capacities = artist_shuffle.calculate_capacities(218, 15)
    # Sizes differ by at most one.
    assert max(capacities) - min(capacities) <= 1
    assert Counter(capacities) == {15: 8, 14: 7}


def test_capacities_evenly_divisible(artist_shuffle):
    capacities = artist_shuffle.calculate_capacities(20, 5)
    assert capacities == [4, 4, 4, 4, 4]


# ---------------------------------------------------------------------------
# distribute_files
# ---------------------------------------------------------------------------


def _library_paths(names):
    from pathlib import Path

    return [Path(name) for name in names]


def test_distribute_places_every_file_exactly_once(artist_shuffle):
    files = _library_paths(
        [f"{artist} - Song {n}.mp3" for artist in "ABC" for n in range(1, 8)]
    )
    capacities = artist_shuffle.calculate_capacities(len(files), 4)
    directories = artist_shuffle.distribute_files(files, capacities)

    placed = [f for directory in directories for f in directory]
    assert sorted(placed) == sorted(files)
    assert len(placed) == len(files)


def test_distribute_respects_capacities(artist_shuffle):
    files = _library_paths(
        [f"{artist} - Song {n}.mp3" for artist in "ABCDE" for n in range(1, 11)]
    )
    capacities = artist_shuffle.calculate_capacities(len(files), 7)
    directories = artist_shuffle.distribute_files(files, capacities)

    for directory, capacity in zip(directories, capacities, strict=True):
        assert len(directory) <= capacity


def test_distribute_spreads_artists_when_possible(artist_shuffle):
    # 5 artists x 5 songs across 5 directories -> ideally one per directory.
    files = _library_paths(
        [f"{artist} - Song {n}.mp3" for artist in "ABCDE" for n in range(1, 6)]
    )
    capacities = artist_shuffle.calculate_capacities(len(files), 5)
    directories = artist_shuffle.distribute_files(files, capacities)

    for directory in directories:
        artists = Counter(artist_shuffle.get_artist(f.name) for f in directory)
        # No artist should repeat within a directory in the ideal case.
        assert all(count == 1 for count in artists.values())


def test_distribute_handles_single_dominant_artist(artist_shuffle):
    # One artist with far more songs than directories must still fit.
    files = _library_paths([f"Solo - Song {n}.mp3" for n in range(1, 21)])
    capacities = artist_shuffle.calculate_capacities(len(files), 4)
    directories = artist_shuffle.distribute_files(files, capacities)

    placed = [f for directory in directories for f in directory]
    assert len(placed) == 20
    # Spread as evenly as the capacities allow (5 each here).
    assert [len(d) for d in directories] == [5, 5, 5, 5]


# ---------------------------------------------------------------------------
# find_input_files
# ---------------------------------------------------------------------------


def test_find_input_files_filters_by_extension(artist_shuffle, make_library):
    library = make_library(
        ["A - x.mp3", "B - y.flac", "notes.txt", "cover.jpg", "C - z.OGG"]
    )
    found = artist_shuffle.find_input_files(library, all_files=False)
    names = {p.name for p in found}
    assert names == {"A - x.mp3", "B - y.flac", "C - z.OGG"}


def test_find_input_files_all_files_mode(artist_shuffle, make_library):
    library = make_library(["A - x.mp3", "notes.txt"])
    found = artist_shuffle.find_input_files(library, all_files=True)
    assert {p.name for p in found} == {"A - x.mp3", "notes.txt"}


def test_find_input_files_is_sorted(artist_shuffle, make_library):
    library = make_library(["C - z.mp3", "A - x.mp3", "B - y.mp3"])
    found = artist_shuffle.find_input_files(library, all_files=False)
    assert [p.name for p in found] == ["A - x.mp3", "B - y.mp3", "C - z.mp3"]


def test_find_input_files_ignores_subdirectories(artist_shuffle, make_library):
    library = make_library(["A - x.mp3"])
    (library / "001").mkdir()
    found = artist_shuffle.find_input_files(library, all_files=True)
    assert {p.name for p in found} == {"A - x.mp3"}


# ---------------------------------------------------------------------------
# check_output_directories
# ---------------------------------------------------------------------------


def test_check_output_directories_allows_missing_and_empty(artist_shuffle, tmp_path):
    (tmp_path / "001").mkdir()  # empty existing dir is fine
    # 002 and 003 do not exist -> also fine
    artist_shuffle.check_output_directories(tmp_path, 3)


def test_check_output_directories_rejects_non_empty(artist_shuffle, tmp_path):
    outdir = tmp_path / "001"
    outdir.mkdir()
    (outdir / "leftover.mp3").touch()
    with pytest.raises(RuntimeError, match="not empty"):
        artist_shuffle.check_output_directories(tmp_path, 1)


def test_check_output_directories_rejects_file_in_the_way(artist_shuffle, tmp_path):
    (tmp_path / "001").touch()  # a file, not a directory
    with pytest.raises(RuntimeError, match="not a directory"):
        artist_shuffle.check_output_directories(tmp_path, 1)


# ---------------------------------------------------------------------------
# prepare_output (end-to-end file operations)
# ---------------------------------------------------------------------------


def test_prepare_output_copy_keeps_sources(artist_shuffle, make_library):
    library = make_library([f"A - Song {n}.mp3" for n in range(1, 7)])
    files = artist_shuffle.find_input_files(library, all_files=False)
    capacities = artist_shuffle.calculate_capacities(len(files), 2)
    directories = artist_shuffle.distribute_files(files, capacities)

    artist_shuffle.prepare_output(library, directories, mode="copy")

    # Sources remain.
    assert len(list(library.glob("*.mp3"))) == 6
    # And copies exist, numbered.
    copied = list(library.glob("00*/*.mp3"))
    assert len(copied) == 6
    # Each copy is prefixed with a zero-padded position, e.g. "001-".
    for f in copied:
        assert f.name[:3].isdigit()
        assert f.name[3] == "-"


def test_prepare_output_move_removes_sources(artist_shuffle, make_library):
    library = make_library([f"A - Song {n}.mp3" for n in range(1, 7)])
    files = artist_shuffle.find_input_files(library, all_files=False)
    capacities = artist_shuffle.calculate_capacities(len(files), 2)
    directories = artist_shuffle.distribute_files(files, capacities)

    artist_shuffle.prepare_output(library, directories, mode="move")

    assert list(library.glob("*.mp3")) == []  # sources gone
    assert len(list(library.glob("00*/*.mp3"))) == 6  # now inside subdirs


def test_prepare_output_reuses_existing_empty_dir(artist_shuffle, make_library):
    library = make_library([f"A - Song {n}.mp3" for n in range(1, 5)])
    (library / "001").mkdir()  # pre-existing empty output dir
    files = artist_shuffle.find_input_files(library, all_files=False)
    capacities = artist_shuffle.calculate_capacities(len(files), 2)
    directories = artist_shuffle.distribute_files(files, capacities)

    # Should not raise despite 001/ already existing.
    artist_shuffle.prepare_output(library, directories, mode="copy")
    assert len(list(library.glob("00*/*.mp3"))) == 4


def test_prepare_output_copy_rolls_back_on_failure(
    artist_shuffle, make_library, monkeypatch
):
    library = make_library([f"A - Song {n}.mp3" for n in range(1, 9)])
    files = artist_shuffle.find_input_files(library, all_files=False)
    capacities = artist_shuffle.calculate_capacities(len(files), 3)
    directories = artist_shuffle.distribute_files(files, capacities)

    calls = {"n": 0}
    real_copy = artist_shuffle.shutil.copy2

    def flaky_copy(src, dst):
        calls["n"] += 1
        if calls["n"] > 3:
            raise OSError("disk full")
        return real_copy(src, dst)

    monkeypatch.setattr(artist_shuffle.shutil, "copy2", flaky_copy)

    with pytest.raises(OSError):
        artist_shuffle.prepare_output(library, directories, mode="copy")

    # Rollback removed every output directory it created.
    assert list(library.glob("00*")) == []
    # Sources are untouched.
    assert len(list(library.glob("*.mp3"))) == 8


# ---------------------------------------------------------------------------
# Reproducibility (end-to-end through main-style flow)
# ---------------------------------------------------------------------------


def test_same_seed_produces_same_layout(artist_shuffle):
    names = [
        f"{artist} - Song {n}.mp3"
        for artist in ["Adele", "Radiohead", "Pixies", "Björk"]
        for n in range(1, 9)
    ]

    def run():
        from pathlib import Path

        random.seed(12345)
        files = sorted((Path(n) for n in names), key=lambda p: p.name)
        capacities = artist_shuffle.calculate_capacities(len(files), 6)
        directories = artist_shuffle.distribute_files(files, capacities)
        return [[f.name for f in d] for d in directories]

    assert run() == run()
