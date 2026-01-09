#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "click",
#   "loguru",
#   "pydantic",
# ]
# ///

import csv
import datetime as dt
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
    print(f"SELECT COUNT(DISTINCT f.idFile) FROM files f WHERE f.strFilename IN (\"{'", "'.join({r.str_filename for r in rows})}\");")
    return 0


if __name__ == "__main__":
    logger.info("Starting")
    rtn: int = main()
    logger.info(f"Exiting with {rtn}")
    sys.exit(rtn)
