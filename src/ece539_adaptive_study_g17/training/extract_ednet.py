#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Aniketh Kancherla
#
# This file header was last modified 27 Nov 2026.
"""Extract a reproducible learner sample without unpacking the entire KT1 ZIP."""

import argparse
import json
import re
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
from zipfile import ZipFile

MIN_LEARNERS = 3


def extract_sample(archive: Path, output: Path, count: int, seed: int) -> None:
    """Copy only validated learner members; publish after extraction succeeds.

    Only learner CSVs are copied. Sampling uses filenames, not learner outcomes.
    """
    if output.exists():
        raise FileExistsError(output)
    if count < MIN_LEARNERS:
        message = "at least three learners required"
        raise ValueError(message)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as source:
        # 1. Collect learner CSVs only. Ignore folders and unrelated ZIP files.
        members = []
        for filename in source.namelist():
            if re.fullmatch(r"(?:KT1/)?u[0-9]+\.csv", filename):
                members.append(filename)
        members.sort()
        if len(members) < count:
            message = "archive contains fewer learners than requested"
            raise ValueError(message)
        Random(seed).shuffle(members)
        selected = sorted(members[:count])
        # 2. Reject files that would overwrite another learner after extraction.
        seen_filenames = set()
        for member_name in selected:
            filename = Path(member_name).name
            if filename in seen_filenames:
                message = "duplicate learner basenames in archive"
                raise ValueError(message)
            seen_filenames.add(filename)
        with TemporaryDirectory(
            prefix="ednet-extract-", dir=output.parent
        ) as temporary:
            # 3. Build in a disposable folder; errors clean it up automatically.
            working_dir = Path(temporary).joinpath("KT1")
            working_dir.mkdir()
            for member_name in selected:
                filename = Path(member_name).name
                destination_path = working_dir.joinpath(filename)
                file_contents = source.read(member_name)
                destination_path.write_bytes(file_contents)
            manifest = {
                "population_learners": len(members),
                "sample_learners": count,
                "seed": seed,
                "selected_members": selected,
            }
            # 4. Save sampling details, then move the finished folder into place.
            manifest_path = working_dir.joinpath("source_manifest.json")
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            working_dir.rename(output)


def main() -> None:
    """Extract a seeded sample of whole learner histories from an official ZIP."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=539)
    arguments = parser.parse_args()
    extract_sample(
        arguments.archive, arguments.output_dir, arguments.count, arguments.seed
    )


if __name__ == "__main__":
    main()
