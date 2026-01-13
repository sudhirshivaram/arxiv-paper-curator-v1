"""
Visualization and reporting for RAG benchmark results.

Creates:
1. Comparison charts for RAGAS scores
2. Latency distribution plots
3. Hit rate visualizations
4. Cost analysis charts
5. HTML report
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkVisualizer:
    """Create visualizations from benchmark results"""

    def __init__(self, results_path: str):
        """Initialize with results JSON file"""
        with open(results_path, "r") as f:
            self.results = json.load(f)

        self.output_dir = Path(results_path).parent / "visualizations"
        self.output_dir.mkdir(exist_ok=True)

    def create_all_visualizations(self):
        """Generate all visualization charts"""
        logger.info("Creating visualizations...")

        self.plot_ragas_scores()
        self.plot_ranking_metrics()
        self.plot_latency_metrics()
        self.plot_cost_metrics()
        self.create_html_report()

        logger.info(f"Visualizations saved to {self.output_dir}")

    def plot_ragas_scores(self):
        """Bar chart of RAGAS scores"""
        ragas = self.results["ragas_scores"]

        # Exclude overall score for individual metrics
        metrics = {k: v for k, v in ragas.items() if k != "ragas_score"}

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(metrics.keys(), metrics.values(), color=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"])

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.3f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        ax.set_ylabel("Score (0-1 scale)", fontsize=12)
        ax.set_title("RAGAS Evaluation Scores", fontsize=14, fontweight="bold")
        ax.set_ylim(0, 1.0)
        ax.axhline(y=0.7, color="green", linestyle="--", alpha=0.3, label="Good (0.7+)")
        ax.axhline(y=0.5, color="orange", linestyle="--", alpha=0.3, label="Fair (0.5+)")
        ax.legend()

        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
        plt.savefig(self.output_dir / "ragas_scores.png", dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("✓ RAGAS scores chart created")

    def plot_ranking_metrics(self):
        """Bar chart of Hit Rate@k metrics"""
        ranking = self.results["ranking_metrics"]

        # Extract Hit Rate metrics
        hit_rates = {k: v for k, v in ranking.items() if "hit_rate" in k}
        mrr = ranking["mrr"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Hit Rate@k chart
        x_labels = [k.replace("hit_rate@", "HR@") for k in hit_rates.keys()]
        values = list(hit_rates.values())

        bars = ax1.bar(x_labels, values, color=["#FF5722", "#FF9800", "#FFC107", "#FFEB3B"])

        for bar in bars:
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1%}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        ax1.set_ylabel("Hit Rate", fontsize=12)
        ax1.set_title("Hit Rate @ k", fontsize=14, fontweight="bold")
        ax1.set_ylim(0, 1.0)

        # MRR gauge chart
        ax2.barh(["MRR"], [mrr], color="#3F51B5", height=0.5)
        ax2.text(mrr / 2, 0, f"{mrr:.3f}", ha="center", va="center", color="white", fontweight="bold", fontsize=16)
        ax2.set_xlim(0, 1.0)
        ax2.set_title("Mean Reciprocal Rank (MRR)", fontsize=14, fontweight="bold")
        ax2.set_xlabel("Score", fontsize=12)

        plt.tight_layout()
        plt.savefig(self.output_dir / "ranking_metrics.png", dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("✓ Ranking metrics chart created")

    def plot_latency_metrics(self):
        """Box plot of latency percentiles"""
        latency = self.results["latency_metrics"]

        fig, ax = plt.subplots(figsize=(10, 6))

        metrics = ["avg_ms", "p50_ms", "p95_ms", "p99_ms"]
        values = [latency[m] for m in metrics]
        labels = ["Average", "P50\n(Median)", "P95", "P99"]

        bars = ax.bar(labels, values, color=["#4CAF50", "#2196F3", "#FF9800", "#F44336"])

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.0f}ms",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        ax.set_ylabel("Latency (milliseconds)", fontsize=12)
        ax.set_title("Query Latency Distribution", fontsize=14, fontweight="bold")

        # Add target latency line (e.g., 500ms)
        ax.axhline(y=500, color="red", linestyle="--", alpha=0.5, label="Target (500ms)")
        ax.legend()

        plt.tight_layout()
        plt.savefig(self.output_dir / "latency_metrics.png", dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("✓ Latency metrics chart created")

    def plot_cost_metrics(self):
        """Cost analysis visualization"""
        cost = self.results["cost_metrics"]
        summary = self.results["summary"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Total tokens used
        ax1.bar(["Total Tokens"], [cost["total_tokens"]], color="#9C27B0", width=0.4)
        ax1.text(
            0,
            cost["total_tokens"] / 2,
            f"{cost['total_tokens']:,}",
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            fontsize=14,
        )
        ax1.set_ylabel("Token Count", fontsize=12)
        ax1.set_title("Total Tokens Used", fontsize=14, fontweight="bold")

        # Cost breakdown
        total_cost = cost["estimated_cost_usd"]
        cost_per_query = total_cost / summary["num_samples"]

        costs = [total_cost, cost_per_query * 1000]  # Scale per-query for visibility
        labels = ["Total Cost\n($)", "Cost per Query\n($ × 1000)"]

        bars = ax2.bar(labels, costs, color=["#4CAF50", "#2196F3"])

        ax2.text(0, total_cost / 2, f"${total_cost:.4f}", ha="center", va="center", fontweight="bold", fontsize=12)
        ax2.text(1, costs[1] / 2, f"${cost_per_query:.6f}", ha="center", va="center", fontweight="bold", fontsize=12)

        ax2.set_ylabel("Cost (USD)", fontsize=12)
        ax2.set_title("Cost Analysis", fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(self.output_dir / "cost_metrics.png", dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("✓ Cost metrics chart created")

    def create_html_report(self):
        """Generate comprehensive HTML report"""
        ragas = self.results["ragas_scores"]
        ranking = self.results["ranking_metrics"]
        latency = self.results["latency_metrics"]
        cost = self.results["cost_metrics"]
        summary = self.results["summary"]

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>RAG Benchmark Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric-label {{
            font-weight: 500;
            color: #666;
        }}
        .metric-value {{
            font-weight: bold;
            color: #333;
        }}
        .score-excellent {{ color: #4CAF50; }}
        .score-good {{ color: #8BC34A; }}
        .score-fair {{ color: #FF9800; }}
        .score-poor {{ color: #F44336; }}
        .chart {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 RAG System Benchmark Report</h1>
        <p>Comprehensive evaluation metrics and analysis</p>
    </div>

    <div class="summary">
        <h2>📋 Evaluation Summary</h2>
        <div class="metric-row">
            <span class="metric-label">Total Samples:</span>
            <span class="metric-value">{summary['num_samples']}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Failed Queries:</span>
            <span class="metric-value">{summary['failed_queries']}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Success Rate:</span>
            <span class="metric-value">{(1 - summary['failed_queries']/summary['num_samples'])*100:.1f}%</span>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h2>✅ RAGAS Scores</h2>
            <div class="metric-row">
                <span class="metric-label">Overall RAGAS Score:</span>
                <span class="metric-value score-{self._get_score_class(ragas.get('ragas_score', 0))}">{ragas.get('ragas_score', 0):.3f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Faithfulness:</span>
                <span class="metric-value score-{self._get_score_class(ragas['faithfulness'])}">{ragas['faithfulness']:.3f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Answer Relevancy:</span>
                <span class="metric-value score-{self._get_score_class(ragas['answer_relevancy'])}">{ragas['answer_relevancy']:.3f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Context Precision:</span>
                <span class="metric-value score-{self._get_score_class(ragas['context_precision'])}">{ragas['context_precision']:.3f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Context Recall:</span>
                <span class="metric-value score-{self._get_score_class(ragas['context_recall'])}">{ragas['context_recall']:.3f}</span>
            </div>
        </div>

        <div class="metric-card">
            <h2>🎯 Ranking Metrics</h2>
            <div class="metric-row">
                <span class="metric-label">MRR:</span>
                <span class="metric-value">{ranking['mrr']:.3f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Hit Rate@1:</span>
                <span class="metric-value">{ranking['hit_rate@1']:.1%}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Hit Rate@3:</span>
                <span class="metric-value">{ranking['hit_rate@3']:.1%}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Hit Rate@5:</span>
                <span class="metric-value">{ranking['hit_rate@5']:.1%}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Hit Rate@10:</span>
                <span class="metric-value">{ranking['hit_rate@10']:.1%}</span>
            </div>
        </div>

        <div class="metric-card">
            <h2>⚡ Latency Metrics</h2>
            <div class="metric-row">
                <span class="metric-label">Average:</span>
                <span class="metric-value">{latency['avg_ms']:.1f} ms</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">P50 (Median):</span>
                <span class="metric-value">{latency['p50_ms']:.1f} ms</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">P95:</span>
                <span class="metric-value">{latency['p95_ms']:.1f} ms</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">P99:</span>
                <span class="metric-value">{latency['p99_ms']:.1f} ms</span>
            </div>
        </div>

        <div class="metric-card">
            <h2>💰 Cost Metrics</h2>
            <div class="metric-row">
                <span class="metric-label">Total Tokens:</span>
                <span class="metric-value">{cost['total_tokens']:,}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Avg Tokens/Query:</span>
                <span class="metric-value">{cost['avg_tokens_per_query']:.1f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total Cost:</span>
                <span class="metric-value">${cost['estimated_cost_usd']:.4f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Cost per Query:</span>
                <span class="metric-value">${cost['estimated_cost_usd']/summary['num_samples']:.6f}</span>
            </div>
        </div>
    </div>

    <h2 style="text-align: center; margin-top: 40px;">📈 Visualizations</h2>

    <div class="chart">
        <h3>RAGAS Scores</h3>
        <img src="ragas_scores.png" alt="RAGAS Scores">
    </div>

    <div class="chart">
        <h3>Ranking Metrics</h3>
        <img src="ranking_metrics.png" alt="Ranking Metrics">
    </div>

    <div class="chart">
        <h3>Latency Distribution</h3>
        <img src="latency_metrics.png" alt="Latency Metrics">
    </div>

    <div class="chart">
        <h3>Cost Analysis</h3>
        <img src="cost_metrics.png" alt="Cost Metrics">
    </div>

    <div class="footer">
        <p>Generated with RAG Benchmarking Framework</p>
        <p>Evaluation Date: {self._get_timestamp()}</p>
    </div>
</body>
</html>
"""

        report_path = self.output_dir / "benchmark_report.html"
        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"✓ HTML report created: {report_path}")
        print(f"\n📄 View full report: file://{report_path.absolute()}")

    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score coloring"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Visualize RAG benchmark results")
    parser.add_argument("results_file", help="Path to benchmark results JSON file")

    args = parser.parse_args()

    visualizer = BenchmarkVisualizer(args.results_file)
    visualizer.create_all_visualizations()

    print("\n✅ All visualizations created successfully!")
    print(f"📁 Output directory: {visualizer.output_dir}")


if __name__ == "__main__":
    main()
