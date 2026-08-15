import argparse
import logging
from pathlib import Path

from .pipeline import collect, load_sources, write_asset


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Daejeon bank branches into a static JSON asset.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output / "bank-branches.json" if args.output.is_dir() else args.output

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    branches, errors = collect(load_sources(args.config))
    if errors:
        for error in errors:
            logging.error(error)
    if not branches:
        logging.error("No valid branches collected; existing output was not replaced.")
        return 1
    write_asset(branches, output)
    logging.info("Wrote %d branches to %s", len(branches), output)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
