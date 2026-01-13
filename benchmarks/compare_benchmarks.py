"""
Compare multiple benchmark runs to track improvements.

This script compares different benchmark results to show:
- Performance improvements/degradations
- Trade-offs between metrics
- Historical trends
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkComparator:
    """Compare multiple benchmark results"""

    def __init__(self, result_files: List[str]):
        """Load multiple benchmark result files"""
        self.results = []
        for file_path in result_files:
            with open(file_path, "r") as f:
                data = json.load(f)
                data["_source_file"] = Path(file_path).name
                self.results.append(data)

        logger.info(f"Loaded {len(self.results)} benchmark results")

    def print_comparison(self):
        """Print side-by-side comparison table"""
        if len(self.results) < 2:
            logger.warning("Need at least 2 results to compare")
            return

        print("\n" + "=" * 120)
        print("BENCHMARK COMPARISON REPORT".center(120))
        print("=" * 120)

        # Print header
        print(f"\n{'Metric':<30}", end="")
        for i, result in enumerate(self.results):
            print(f"{'Run ' + str(i+1):>20}", end="")
        print(f"{'Change':>20}")
        print("-" * 120)

        # RAGAS Scores
        print("\n📊 RAGAS SCORES")
        print("-" * 120)
        self._compare_metric("Overall RAGAS", lambda r: r["ragas_scores"].get("ragas_score", 0.0))
        self._compare_metric("Faithfulness", lambda r: r["ragas_scores"]["faithfulness"])
        self._compare_metric("Answer Relevancy", lambda r: r["ragas_scores"]["answer_relevancy"])
        self._compare_metric("Context Precision", lambda r: r["ragas_scores"]["context_precision"])
        self._compare_metric("Context Recall", lambda r: r["ragas_scores"]["context_recall"])

        # Ranking Metrics
        print("\n🎯 RANKING METRICS")
        print("-" * 120)
        self._compare_metric("MRR", lambda r: r["ranking_metrics"]["mrr"])
        self._compare_metric("Hit Rate@1", lambda r: r["ranking_metrics"]["hit_rate@1"], as_percentage=True)
        self._compare_metric("Hit Rate@3", lambda r: r["ranking_metrics"]["hit_rate@3"], as_percentage=True)
        self._compare_metric("Hit Rate@5", lambda r: r["ranking_metrics"]["hit_rate@5"], as_percentage=True)
        self._compare_metric("Hit Rate@10", lambda r: r["ranking_metrics"]["hit_rate@10"], as_percentage=True)

        # Latency Metrics
        print("\n⚡ LATENCY METRICS (ms)")
        print("-" * 120)
        self._compare_metric("Average Latency", lambda r: r["latency_metrics"]["avg_ms"], suffix=" ms")
        self._compare_metric("P50 Latency", lambda r: r["latency_metrics"]["p50_ms"], suffix=" ms")
        self._compare_metric("P95 Latency", lambda r: r["latency_metrics"]["p95_ms"], suffix=" ms")
        self._compare_metric("P99 Latency", lambda r: r["latency_metrics"]["p99_ms"], suffix=" ms")

        # Cost Metrics
        print("\n💰 COST METRICS")
        print("-" * 120)
        self._compare_metric("Total Tokens", lambda r: r["cost_metrics"]["total_tokens"], as_int=True)
        self._compare_metric("Avg Tokens/Query", lambda r: r["cost_metrics"]["avg_tokens_per_query"])
        self._compare_metric("Total Cost (USD)", lambda r: r["cost_metrics"]["estimated_cost_usd"], prefix="$")

        # Summary Statistics
        print("\n📈 IMPROVEMENT SUMMARY")
        print("-" * 120)
        self._print_improvement_summary()

        print("\n" + "=" * 120 + "\n")

    def _compare_metric(
        self,
        label: str,
        extractor: callable,
        as_percentage: bool = False,
        as_int: bool = False,
        prefix: str = "",
        suffix: str = "",
    ):
        """Compare a single metric across all results"""
        print(f"{label:<30}", end="")

        values = []
        for result in self.results:
            try:
                value = extractor(result)
                values.append(value)

                # Format value
                if as_percentage:
                    print(f"{value:>19.1%}", end=" ")
                elif as_int:
                    print(f"{prefix}{int(value):>19,}{suffix}", end=" ")
                else:
                    print(f"{prefix}{value:>19.2f}{suffix}", end=" ")
            except (KeyError, TypeError) as e:
                print(f"{'N/A':>20}", end="")
                values.append(None)

        # Calculate change (first to last)
        if len(values) >= 2 and values[0] is not None and values[-1] is not None:
            change = values[-1] - values[0]
            pct_change = (change / values[0] * 100) if values[0] != 0 else 0

            # Determine if change is good (depends on metric)
            is_improvement = self._is_improvement(label, change)

            # Color code the change
            symbol = "🟢" if is_improvement else "🔴" if change != 0 else "⚪"

            if as_percentage:
                print(f"{symbol} {change:>8.1%} ({pct_change:+.1f}%)")
            elif as_int:
                print(f"{symbol} {int(change):>8,} ({pct_change:+.1f}%)")
            else:
                print(f"{symbol} {change:>8.2f} ({pct_change:+.1f}%)")
        else:
            print()

    def _is_improvement(self, label: str, change: float) -> bool:
        """Determine if a change is an improvement"""
        # Metrics where higher is better
        higher_is_better = [
            "RAGAS",
            "Faithfulness",
            "Relevancy",
            "Precision",
            "Recall",
            "MRR",
            "Hit Rate",
        ]

        # Metrics where lower is better
        lower_is_better = ["Latency", "Cost", "Tokens"]

        for keyword in higher_is_better:
            if keyword in label:
                return change > 0

        for keyword in lower_is_better:
            if keyword in label:
                return change < 0

        return change > 0  # Default: assume higher is better

    def _print_improvement_summary(self):
        """Print summary of improvements"""
        if len(self.results) < 2:
            return

        first = self.results[0]
        last = self.results[-1]

        improvements = []
        degradations = []

        # Check key metrics
        metrics_to_check = [
            ("RAGAS Score", lambda r: r["ragas_scores"].get("ragas_score", 0), True),
            ("MRR", lambda r: r["ranking_metrics"]["mrr"], True),
            ("Hit Rate@5", lambda r: r["ranking_metrics"]["hit_rate@5"], True),
            ("Avg Latency (ms)", lambda r: r["latency_metrics"]["avg_ms"], False),
            ("Total Cost ($)", lambda r: r["cost_metrics"]["estimated_cost_usd"], False),
        ]

        for label, extractor, higher_is_better in metrics_to_check:
            try:
                first_val = extractor(first)
                last_val = extractor(last)
                change = last_val - first_val
                pct_change = (change / first_val * 100) if first_val != 0 else 0

                is_improvement = (change > 0) if higher_is_better else (change < 0)

                if abs(pct_change) > 1:  # Only show significant changes
                    msg = f"{label}: {pct_change:+.1f}% ({first_val:.3f} → {last_val:.3f})"
                    if is_improvement:
                        improvements.append(msg)
                    else:
                        degradations.append(msg)
            except (KeyError, TypeError):
                pass

        if improvements:
            print("\n✅ Improvements:")
            for imp in improvements:
                print(f"   • {imp}")

        if degradations:
            print("\n⚠️  Degradations:")
            for deg in degradations:
                print(f"   • {deg}")

        if not improvements and not degradations:
            print("\n⚪ No significant changes detected")

    def export_comparison(self, output_path: str):
        """Export comparison to JSON"""
        comparison_data = {
            "results": self.results,
            "summary": self._generate_summary(),
        }

        with open(output_path, "w") as f:
            json.dump(comparison_data, f, indent=2)

        logger.info(f"Comparison exported to {output_path}")

    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        if len(self.results) < 2:
            return {}

        first = self.results[0]
        last = self.results[-1]

        return {
            "num_runs": len(self.results),
            "ragas_improvement": last["ragas_scores"].get("ragas_score", 0)
            - first["ragas_scores"].get("ragas_score", 0),
            "mrr_improvement": last["ranking_metrics"]["mrr"] - first["ranking_metrics"]["mrr"],
            "latency_improvement_ms": first["latency_metrics"]["avg_ms"] - last["latency_metrics"]["avg_ms"],
            "cost_reduction_usd": first["cost_metrics"]["estimated_cost_usd"]
            - last["cost_metrics"]["estimated_cost_usd"],
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Compare multiple benchmark results")
    parser.add_argument("result_files", nargs="+", help="Paths to benchmark result JSON files")
    parser.add_argument("--export", help="Export comparison to JSON file")

    args = parser.parse_args()

    if len(args.result_files) < 2:
        print("❌ Error: Need at least 2 result files to compare")
        return

    comparator = BenchmarkComparator(args.result_files)
    comparator.print_comparison()

    if args.export:
        comparator.export_comparison(args.export)
        print(f"\n📁 Comparison exported to: {args.export}")


if __name__ == "__main__":
    main()
