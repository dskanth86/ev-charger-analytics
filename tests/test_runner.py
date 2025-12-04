"""EV-Charger Analytics test automation runner.

Runs large-scale, black-box testing of the end-to-end analytics
pipeline using sampled ZIP codes and synthetic addresses.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import List

from .zip_sampling import generate_zip_samples
from .pipeline_harness import PipelineInputs, run_pipeline_for_zip
from .validators import validate_pipeline_output
from .jitter_tests import run_jitter_stability
from .reporting import (
    write_anomalies_csv,
    write_benchmark_stats_json,
    generate_results_pdf,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EV-Charger Analytics pipeline test runner",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_outputs",
        help="Directory where test artifacts (PDF, CSV, JSON) will be written.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Number of ZIP samples to run (<= total available).",
    )
    parser.add_argument(
        "--jitter-per-zip",
        type=int,
        default=0,
        help="Number of jitter stability runs per ZIP (0 to disable).",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[tests] Output directory: {output_dir}")

    # 1) ZIP sampling
    zip_samples = generate_zip_samples(target_count=max(500, args.sample_size))
    zip_samples = zip_samples[: args.sample_size]
    total = len(zip_samples)
    print(f"[tests] Running pipeline for {total} ZIP samples...")

    records: List[dict] = []
    anomalies_all: List[dict] = []

    for i, z in enumerate(zip_samples, start=1):
        print(f"[tests] [{i}/{total}] Running pipeline for ZIP {z.zip_code} ({z.tag})...")
        base_inputs = PipelineInputs(address=f"123 Main St, {z.state} {z.zip_code}, USA")

        try:
            out = run_pipeline_for_zip(z, inputs=base_inputs)
        except Exception as exc:  # noqa: BLE001 - test harness should be robust
            print(f"[tests]   !! Error for ZIP {z.zip_code}: {exc}. Skipping.")
            continue

        data = out.to_dict()

        # Attach ZIP metadata for later aggregation
        data.update(
            {
                "zip_code": z.zip_code,
                "state": z.state,
                "region_type": z.region_type,
                "income_band": z.income_band,
                "ev_share_band": z.ev_share_band,
                "tag": z.tag,
            }
        )

        records.append(data)

        # 4) Validate ranges & detect anomalies (base run only)
        anomalies = validate_pipeline_output(z, data)
        anomalies_all.extend(asdict(a) for a in anomalies)

        # 7) Stability tests via jitter
        if args.jitter_per_zip > 0:
            jitter_records = run_jitter_stability(z, base_inputs, n=args.jitter_per_zip)
            for jr in jitter_records:
                jr.update(
                    {
                        "zip_code": z.zip_code,
                        "state": z.state,
                        "region_type": z.region_type,
                        "income_band": z.income_band,
                        "ev_share_band": z.ev_share_band,
                        "tag": z.tag,
                    }
                )
            records.extend(jr for jr in jitter_records)

        if i % 25 == 0:
            print(f"[tests] Progress: processed {i} / {total} ZIPs")

    # 5) Anomalies listing
    anomalies_csv = output_dir / "anomalies.csv"
    print("[tests] Writing anomalies CSV...")
    write_anomalies_csv(anomalies_csv, anomalies_all)
    print(f"[tests] Anomalies written to {anomalies_csv}")

    # 6) Statistical analyses & 8) benchmark_stats.json
    stats_json = output_dir / "benchmark_stats.json"
    print("[tests] Computing benchmark statistics and correlations...")
    stats = write_benchmark_stats_json(stats_json, records)
    print(f"[tests] Benchmark stats written to {stats_json}")

    # 8) EV_Analytics_Test_Results.pdf
    results_pdf = output_dir / "EV_Analytics_Test_Results.pdf"
    print("[tests] Generating summary PDF...")
    generate_results_pdf(results_pdf, records, stats)
    print(f"[tests] Results PDF written to {results_pdf}")


if __name__ == "__main__":
    main()
