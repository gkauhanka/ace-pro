from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .metrics import combine_evaluations, evaluate_ball_tracking
from .overlay import render_ball_overlay
from .schema import (
    SCHEMA_VERSION,
    SchemaError,
    load_dataset_manifest,
    load_observations,
    validate_dataset,
)
from .tracknet import normalize_tracknet_csv, run_tracknet


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, SchemaError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ace-eval")
    commands = parser.add_subparsers(required=True)

    normalize = commands.add_parser("normalize-tracknet", help="normalize an upstream CSV")
    normalize.add_argument("--csv", type=Path, required=True)
    normalize.add_argument("--output", type=Path, required=True)
    normalize.add_argument("--fps", type=float, required=True)
    normalize.add_argument("--video", type=Path)
    normalize.add_argument("--weights", type=Path)
    normalize.set_defaults(handler=_normalize_tracknet)

    run = commands.add_parser("run-tracknet", help="run the pinned TrackNetV4 adapter")
    run.add_argument("--video", type=Path, required=True)
    run.add_argument("--repository", type=Path, required=True)
    run.add_argument("--weights", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--fps", type=float, help="override FPS; otherwise ffprobe reads the video")
    run.add_argument("--python", type=Path)
    run.add_argument("--allow-revision-mismatch", action="store_true")
    run.set_defaults(handler=_run_tracknet)

    evaluate = commands.add_parser("evaluate", help="evaluate one prediction artifact")
    evaluate.add_argument("--ground-truth", type=Path, required=True)
    evaluate.add_argument("--predictions", type=Path, required=True)
    evaluate.add_argument("--tolerance-px", type=float, default=10)
    evaluate.add_argument("--output", type=Path, required=True)
    evaluate.set_defaults(handler=_evaluate)

    dataset = commands.add_parser("validate-dataset", help="validate schema and split leakage")
    dataset.add_argument("--dataset", type=Path, required=True)
    dataset.add_argument("--allow-missing-files", action="store_true")
    dataset.set_defaults(handler=_validate_dataset)

    evaluate_dataset = commands.add_parser(
        "evaluate-dataset", help="evaluate <sequence_id>.jsonl artifacts"
    )
    evaluate_dataset.add_argument("--dataset", type=Path, required=True)
    evaluate_dataset.add_argument("--predictions-dir", type=Path, required=True)
    evaluate_dataset.add_argument(
        "--split", choices=["train", "validation", "test"], default="test"
    )
    evaluate_dataset.add_argument("--tolerance-px", type=float, default=10)
    evaluate_dataset.add_argument("--output", type=Path, required=True)
    evaluate_dataset.set_defaults(handler=_evaluate_dataset)

    overlay = commands.add_parser("render-overlay", help="render prediction dots on a video")
    overlay.add_argument("--video", type=Path, required=True)
    overlay.add_argument("--predictions", type=Path, required=True)
    overlay.add_argument("--output", type=Path, required=True)
    overlay.set_defaults(handler=_render_overlay)
    return parser


def _normalize_tracknet(args: argparse.Namespace) -> int:
    manifest = normalize_tracknet_csv(
        args.csv,
        args.output,
        fps=args.fps,
        source_video=args.video,
        checkpoint_path=args.weights,
    )
    print(json.dumps({"predictions": str(args.output), "manifest": str(manifest)}))
    return 0


def _run_tracknet(args: argparse.Namespace) -> int:
    predictions, manifest, overlay = run_tracknet(
        video_path=args.video,
        repository_path=args.repository,
        weights_path=args.weights,
        output_dir=args.output_dir,
        fps=args.fps,
        python_executable=args.python,
        allow_revision_mismatch=args.allow_revision_mismatch,
    )
    print(
        json.dumps(
            {"predictions": str(predictions), "manifest": str(manifest), "overlay": str(overlay)}
        )
    )
    return 0


def _evaluate(args: argparse.Namespace) -> int:
    evaluation = evaluate_ball_tracking(
        load_observations(args.ground_truth),
        load_observations(args.predictions),
        tolerance_px=args.tolerance_px,
    )
    report = _report_header(args.tolerance_px)
    report["metrics"] = evaluation.to_dict(tolerance_px=args.tolerance_px)
    _write_report(args.output, report)
    print(json.dumps(report["metrics"], indent=2))
    return 0


def _validate_dataset(args: argparse.Namespace) -> int:
    manifest = load_dataset_manifest(args.dataset)
    errors = validate_dataset(manifest, require_files=not args.allow_missing_files)
    result = {
        "valid": not errors,
        "dataset": manifest.dataset_name,
        "version": manifest.dataset_version,
        "sequence_count": len(manifest.sequences),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def _evaluate_dataset(args: argparse.Namespace) -> int:
    manifest = load_dataset_manifest(args.dataset)
    errors = validate_dataset(manifest)
    if errors:
        raise ValueError("invalid dataset:\n- " + "\n- ".join(errors))
    sequence_reports: list[dict[str, Any]] = []
    evaluations = []
    for sequence in manifest.sequences:
        if sequence.split != args.split:
            continue
        prediction_path = args.predictions_dir / f"{sequence.sequence_id}.jsonl"
        if not prediction_path.is_file():
            raise ValueError(f"predictions not found: {prediction_path}")
        evaluation = evaluate_ball_tracking(
            load_observations(sequence.ground_truth_path),
            load_observations(prediction_path),
            tolerance_px=args.tolerance_px,
        )
        evaluations.append(evaluation)
        sequence_reports.append(
            {
                "sequence_id": sequence.sequence_id,
                "match_id": sequence.match_id,
                "player_id": sequence.player_id,
                "metrics": evaluation.to_dict(tolerance_px=args.tolerance_px),
            }
        )
    if not evaluations:
        raise ValueError(f"dataset has no sequences in split {args.split!r}")
    report = _report_header(args.tolerance_px)
    report.update(
        {
            "dataset": {
                "name": manifest.dataset_name,
                "version": manifest.dataset_version,
                "annotation_guide_version": manifest.annotation_guide_version,
                "split": args.split,
            },
            "metrics": combine_evaluations(evaluations).to_dict(
                tolerance_px=args.tolerance_px
            ),
            "sequences": sequence_reports,
        }
    )
    _write_report(args.output, report)
    print(json.dumps(report["metrics"], indent=2))
    return 0


def _render_overlay(args: argparse.Namespace) -> int:
    render_ball_overlay(args.video, load_observations(args.predictions), args.output)
    print(json.dumps({"overlay": str(args.output)}))
    return 0


def _report_header(tolerance_px: float) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "ball_tracking_evaluation",
        "created_at": datetime.now(UTC).isoformat(),
        "metric_definition": {
            "match_key": "frame_index",
            "true_positive": f"both visible and Euclidean error <= {tolerance_px}px",
            "localization_miss": "both visible outside tolerance; counts as one FP and one FN",
        },
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
