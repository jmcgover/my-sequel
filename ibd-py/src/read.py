#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "click",
#   "jmcgover-ibd-parser",
#   "pyyaml",
#   "tabulate",
#   "flask",
# ]
# [tool.uv.sources]
# jmcgover-ibd-parser = { git = "https://github.com/jmcgover/ibd-parser" }
# ///

import csv
import json
import pathlib
from pprint import pprint

import click
from ibd_parser import IBDFileParser
from tabulate import tabulate
import yaml


def load_schema(schema_path: pathlib.Path) -> dict:
    with schema_path.open("r") as file:
        return yaml.safe_load(file)


def format_mysql_style(records, headers):
    """Format records in MySQL style output"""
    # Convert records to list of lists for tabulate
    table = [record.data for record in records]
    # Use 'psql' format which is close to MySQL style
    return tabulate(
        table,
        headers="keys",
        tablefmt="psql",
        numalign="left",  # Left align numbers like MySQL
        stralign="left",  # Left align strings
    )


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "show_default": True,
        "max_content_width": 120,
    }
)
@click.option(
    "-f",
    "--filename",
    "ibd_path",
    type=click.Path(
        file_okay=True,
        readable=True,
        dir_okay=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="path to IBD file",
)
@click.option(
    "-o",
    "--outfile",
    "out_path",
    type=click.Path(
        path_type=pathlib.Path,
    ),
    required=True,
    help="path to IBD file",
)
@click.option(
    "--schema",
    "schema_path",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="path to corresponding schema file",
)
@click.option(
    "--page",
    "page_no",
    type=int,
    required=True,
    help="page number to analyze",
)
def main(
    ibd_path: pathlib.Path,
    schema_path: pathlib.Path,
    page_no: int,
    out_path: pathlib.Path,
):
    # Parse schema file
    schema = load_schema(schema_path)

    # Initialize parser with .ibd and corresponding schema file
    ibd_parser = IBDFileParser(str(ibd_path), schema=schema)

    # Analyze a specific page
    result = ibd_parser.page_dump(page_no=page_no)
    print("file header:")
    print(result["header"].format())
    print("\nfile trailer:")
    print(result["trailer"].format())

    if "page_header" in result:
        print("\npage header:")
        print(result["page_header"].format_as_string())
    if "page_directory" in result:
        print("\npage directory:")
        pprint(result["page_directory"])
    if "records" in result:
        print("\nrecords:")
        # print(format_mysql_style(result["records"], schema["fields"]))
        for r in result.get("records", []):
            # print(f"{r.record_type=}")
            for k, v in r.data.items():
                print(f"{k}: ({type(v)})'{v}'")
            print(f"{r.error=!s}")
    else:
        print("\nNO records:")

    print(json.dumps(result, indent=2, sort_keys=True, default=str))

    print("=" * 10 + "Parseable:")
    parsed = []
    for r in result.get("records", []):
        if r.data:
            print(json.dumps(r.data, indent=2, sort_keys=True, default=str))
            parsed.append(r.data)

    if len(parsed) > 0:
        print(f"Parsed this many records: {len(parsed):,}")
        this_out_path = out_path.with_stem(f"{out_path.stem}_{page_no:03}")
        fieldnames: set[str] = set()
        for d in parsed:
            fieldnames.update(d.keys())
        print(f"{sorted(fieldnames)=}")
        print(f"Saving to {this_out_path!s}...")
        with this_out_path.open("w") as file:
            writer = csv.DictWriter(file, fieldnames=sorted(fieldnames))
            writer.writeheader()
            for d in parsed:
                writer.writerow(d)

    else:
        print(f"Parsed ZERO records")

    return 0


if __name__ == "__main__":
    main()
