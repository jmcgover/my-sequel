#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "lxml",
#   "requests",
#   "loguru",
# ]
# ///


from argparse import ArgumentParser
import pathlib
import plistlib
import sys

from loguru import logger
from lxml import etree
import requests

DESCRIPTION: str = """Extracts links from an NFO file and determines stuff about it."""


def main() -> int:
    parser = ArgumentParser(prog=sys.argv[0], description=DESCRIPTION)
    parser.add_argument(
        metavar="<movie_metadata.nfo>", type=pathlib.Path, dest="nfo_path", help="path to NFO of movie metadata"
    )
    args = parser.parse_args()
    # Parse Tree
    tree = etree.parse(args.nfo_path)
    bad_parent_child_nodes = []
    root = tree.getroot()
    # Check thumb URLs
    for node in root.iter("thumb"):
        status_code = requests.head(node.text).status_code
        if status_code != 200:
            logger.error(f"BAD ({status_code}): {node.text}")
            parent = node.getparent()
            bad_parent_child_nodes.append(
                (
                    parent,
                    node,
                )
            )

        else:
            logger.info(f"GOOD({status_code}): {node.text}")

    # Return early if all are good
    if len(bad_parent_child_nodes) == 0:
        logger.info("None to remove!")
        return 0

    # Remove bad URLs and relevant parents from tree
    logger.info(f"Removing {len(bad_parent_child_nodes)} nodes")
    for parent, child in bad_parent_child_nodes:
        logger.info(f"Removing {child.tag=}: {child.text=} from {parent.tag=}")
        parent.remove(child)
        if len(parent.getchildren()) == 0:
            grandparent = parent.getparent()
            logger.warning(f"Pruning {parent.tag=}: {parent.getchildren()=} from {grandparent.tag=}")
            grandparent.remove(parent)

    # Create the parent dir
    outfile: pathlib.Path = pathlib.Path.cwd().joinpath("updated", args.nfo_path.parent, args.nfo_path.name)
    logger.info(f"Creating directory {outfile.parent!s}")
    outfile.parent.mkdir(parents=True, exist_ok=True)

    # Save the new file
    logger.info(f"Saving to {outfile!s}")
    with outfile.open("w") as file:
        print(etree.tostring(tree, encoding="unicode", pretty_print=True), file=file)

    return 0


if __name__ == "__main__":
    rtn: int = main()
    logger.info("DONE")
    sys.exit(rtn)
