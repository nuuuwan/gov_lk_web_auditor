from __future__ import annotations

import argparse
from pathlib import Path

from .DashboardBuilder import DashboardBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static audit dashboard")
    parser.add_argument("--reports", default="latest_audit_reports")
    parser.add_argument("--output", default="site")
    parser.add_argument("--directory", default="static_data/websites.json")
    args = parser.parse_args()
    result = DashboardBuilder().build(
        Path(args.reports), Path(args.output), Path(args.directory)
    )
    summary = result["summary"]
    print(
        f"Dashboard: {result['sites']} sites, "
        f"average {summary['average_score']:.1f}/{summary['max_score']} "
        f"-> {args.output}"
    )
    for error in result["errors"]:
        print(f"Skipped {error['host']}: {error['message']}")


if __name__ == "__main__":
    main()
