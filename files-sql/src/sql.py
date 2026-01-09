#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "click",
#   "loguru",
#   "pydantic",
# ]
# ///

from collections import defaultdict
import csv
import datetime as dt
import json
import pathlib
import sqlite3
import sys

import click
from loguru import logger
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel


class FileRow(BaseModel):
    """Entry in the files table for Kodi."""

    model_config = ConfigDict(alias_generator=to_camel)

    id: int
    id_path: int
    str_filename: str
    play_count: int
    last_played: dt.datetime
    date_added: dt.datetime


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "show_default": True,
        "max_content_width": 120,
    }
)
@click.option(
    "--database",
    "db_path",
    type=click.Path(
        file_okay=True,
        readable=True,
        dir_okay=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="path to database file",
)
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(
        file_okay=True,
        readable=True,
        dir_okay=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="path to csv file",
)
def main(
    db_path: pathlib.Path,
    csv_path: pathlib.Path,
) -> int:
    logger.info(f"Opening DB at {db_path!s}...")
    conn = sqlite3.connect(db_path)
    logger.info(f"Opening DB at {db_path!s}...DONE")

    logger.info(f"Opening CSV at {csv_path!s}...")
    rows: list[FileRow] = []
    failed_rows: list[dict] = []
    with csv_path.open("r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                rows.append(FileRow(**row))
            except ValidationError as e:
                failed_rows.append(row)
                logger.error(f"Failed to parse {row=}")
    logger.info(f"Opening CSV at {csv_path!s}...DONE")

    logger.info(f"Successfully parsed {len(rows)=:,}")
    if len(failed_rows) > 0:
        logger.error(f"Failed to parse {len(failed_rows)=:,}")
    print(
        f"SELECT COUNT(DISTINCT f.idFile) FROM files f WHERE f.strFilename IN (\"{'", "'.join({r.str_filename for r in rows})}\");"
    )

    logger.info("Checking for duplicates...")
    path_to_rows: dict[str, list[FileRow]] = defaultdict(list)
    for r in rows:
        path_to_rows[r.str_filename].append(r)

    num_duped_paths: int = 0
    for str_filename, instances in path_to_rows.items():
        if len(instances) > 1:
            logger.warning(f"Found duplicates for {str_filename=}: {len(instances)}")
            print(json.dumps([i.model_dump(mode="json") for i in instances], indent=2), file=sys.stderr)
            num_duped_paths += 1

    logger.info("Checking for duplicates...DONE")
    if num_duped_paths > 0:
        logger.error(f"Found {num_duped_paths=}")
    return 0


if __name__ == "__main__":
    logger.info("Starting")
    rtn: int = main()
    logger.info(f"Exiting with {rtn}")
    sys.exit(rtn)
