import csv
from pathlib import Path
from typing import Dict, Optional
import structlog
import matplotlib.pyplot as plt

from scripts.config import Config


class ResultsParser:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()

    def save_csv(self,
                 results: Dict[str, float],
                 run_id: str) -> Path:
        csv_file = Config.RESULTS_DIR / f"metrics_{run_id}.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("saving_csv",
                         path=str(csv_file),
                         test_count=len(results))

        try:
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Test", "Time_sec", "Run_ID"])
                for test_name, elapsed_time in results.items():
                    writer.writerow([test_name, elapsed_time, run_id])

            self.logger.info("csv_saved",
                             path=str(csv_file),
                             test_count=len(results))
            return csv_file

        except Exception as e:
            self.logger.error("csv_save_failed",
                              path=str(csv_file),
                              error=str(e))
            raise

    def generate_graph(self,
                       results: Dict[str, float],
                       run_id: str) -> Path:
        output_path = Config.GRAPHS_DIR / f"benchmark_chart_{run_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("generating_graph",
                         path=str(output_path),
                         test_count=len(results))

        try:
            tests = list(results.keys())
            times = list(results.values())

            plt.figure(figsize=(12, 6))
            bars = plt.bar(tests, times, color="skyblue", edgecolor="navy", alpha=0.7)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{height:.2f}s',
                         ha='center', va='bottom', fontsize=9)

            plt.ylabel("Time (seconds)", fontsize=12)
            plt.xlabel("Benchmark Test", fontsize=12)
            plt.title(f"Filesystem Benchmark Results - {run_id}", fontsize=14, fontweight="bold")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis='y', alpha=0.3, linestyle='--')
            plt.tight_layout()

            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info("graph_generated",
                             path=str(output_path))
            return output_path

        except Exception as e:
            self.logger.error("graph_generation_failed",
                              path=str(output_path),
                              error=str(e))
            raise