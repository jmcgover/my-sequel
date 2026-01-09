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
from typing import Self

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


class FileRowUpdate(BaseModel):
    """Entry in the files table for Kodi."""

    model_config = ConfigDict(alias_generator=to_camel)

    str_filename: str
    play_count: int
    last_played: dt.datetime

    def update_sql(
        self,
    ) -> str:
        return 'UPDATE files\n  SET\n    lastPlayed="{last_played}",\n    playCount={play_count}\n  WHERE\n    strFilename="{str_filename}"\n;'.format(
            last_played=self.last_played.strftime("%Y-%m-%d %H:%M:%S"),
            play_count=self.play_count,
            str_filename=self.str_filename,
        )

    @classmethod
    def from_rows(cls, rows: list[FileRow]) -> Self:
        str_filenames = {r.str_filename for r in rows}
        assert len(str_filenames) == 1
        return cls(
            strFilename=str_filenames.pop(),
            playCount=sum([r.play_count for r in rows]),
            lastPlayed=max([r.last_played for r in rows]),
        )


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

    update_infos: dict[str, FileRowUpdate] = {}
    num_duped_paths: int = 0
    for str_filename, instances in path_to_rows.items():
        if len(instances) > 1:
            logger.warning(f"Found duplicates for {str_filename=}: {len(instances)}")
            print(json.dumps([i.model_dump(mode="json") for i in instances], indent=2), file=sys.stderr)
            num_duped_paths += 1
        update_infos[str_filename] = FileRowUpdate.from_rows(instances)

    logger.info("Checking for duplicates...DONE")
    logger.info(f"Total rows: {len(rows):,}")
    if num_duped_paths > 0:
        logger.error(f"Duped Paths: {num_duped_paths:,}")
    logger.info(f"Updates to make: {len(update_infos):,}")

    for str_filename, update in update_infos.items():
        assert str_filename == update.str_filename
        logger.info(
            f"{update.str_filename=}, {update.last_played.strftime("%Y-%m-%d %H:%M:%S")=}, {update.play_count=}"
        )
        sql_script_path = pathlib.Path.cwd().joinpath("sql", str_filename).with_suffix(".sql")
        logger.info(f"Saving SQL to {sql_script_path!s}...")
        with sql_script_path.open("w") as file:
            print(update.update_sql(), file=file)
        logger.info(f"Saving SQL to {sql_script_path!s}...DONE")

    return 0


if __name__ == "__main__":
    logger.info("Starting")
    rtn: int = main()
    logger.info(f"Exiting with {rtn}")
    sys.exit(rtn)
