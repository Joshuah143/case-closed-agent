"""Command-line interface with explicit protection for scored seeds."""

from __future__ import annotations

import argparse
import json

from .solver import CaseSolver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Investigate a Case Closed mystery")
    parser.add_argument("seed", nargs="?", default="S001", help="Seed ID, e.g. S001")
    parser.add_argument("--commit", action="store_true", help="Submit the generated verdict")
    parser.add_argument(
        "--submit-hidden",
        action="store_true",
        help="Acknowledge that a scored H00X commit uses the team's single allowed submission",
    )
    parser.add_argument(
        "--present-limit", type=int, default=16, help="Maximum evidence-presentation probes"
    )
    parser.add_argument("--quiet", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = CaseSolver(verbose=not args.quiet).investigate(
        args.seed.upper(),
        commit=args.commit,
        allow_hidden_commit=args.submit_hidden,
        present_limit=max(0, args.present_limit),
    )
    summary = {
        "seed_id": result.seed_id,
        "culprit_id": result.culprit.id,
        "means_id": result.means.id,
        "clues": {clue.clue_id: clue.text for clue in result.clues},
        "inventory": sorted(result.inventory),
        "actions_remaining": result.actions_remaining,
        "evidence_notes": result.evidence_notes,
        "process_explanation": result.process_explanation,
        "commit_result": result.commit_result,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
