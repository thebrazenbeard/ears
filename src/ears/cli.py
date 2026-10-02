from __future__ import annotations

import argparse
import json
from pathlib import Path

from .counterfactual import compare_acoustic_counterfactual
from .pipeline import inspect_wav
from .serialization import write_artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ears",
        description="Build an evidence-preserving acoustic timeline from PCM WAV audio.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect", help="inspect a WAV file")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--out", type=Path, default=Path("ears-artifact"))
    inspect.add_argument("--frame-ms", type=float, default=20.0)
    inspect.add_argument("--hop-ms", type=float, default=10.0)

    compare = subparsers.add_parser(
        "compare",
        help="compare two audio sources without treating lexical equivalence as verified",
    )
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    compare.add_argument("--lexical-control", type=str, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        timeline = inspect_wav(
            args.input,
            frame_ms=args.frame_ms,
            hop_ms=args.hop_ms,
        )
        manifest, evidence = write_artifact(timeline, args.out)
        print(
            json.dumps(
                {
                    "source_id": timeline.source_id,
                    "duration_ms": round(timeline.duration_ms, 3),
                    "evidence_count": len(timeline.evidence),
                    "kind_counts": timeline.kind_counts(),
                    "manifest": str(manifest),
                    "evidence": str(evidence),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "compare":
        left = inspect_wav(args.left)
        right = inspect_wav(args.right)
        print(
            json.dumps(
                compare_acoustic_counterfactual(
                    left,
                    right,
                    lexical_control=args.lexical_control,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())