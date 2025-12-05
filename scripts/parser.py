"""
Enhanced results parser with support for new metrics and system info.
"""
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
import structlog
import matplotlib.pyplot as plt
import numpy as np

from scripts.config import Config


class ResultsParser:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()

    def save_csv(self,
                 results: Dict,
                 system_info: Dict,
                 run_id: str) -> Path:
        """Save detailed results to CSV"""
        csv_file = Config.RESULTS_DIR / f"metrics_{run_id}.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("saving_csv", path=str(csv_file))

        try:
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow([
                    "Test_Name", "File_Size_MB", "Elapsed_Sec",
                    "Throughput_MBps", "IOPS", "Operations",
                    "Latency_P50", "Latency_P95", "Latency_P99",
                    "Run_ID"
                ])

                # Sequential write results
                for metric in results["sequential_write"]:
                    self._write_metric_row(writer, metric, run_id)

                # Sequential read results
                for metric in results["sequential_read"]:
                    self._write_metric_row(writer, metric, run_id)

                # Random R/W results
                if results["random_rw"]:
                    self._write_metric_row(writer, results["random_rw"], run_id)

                # Metadata results
                if results["metadata"]:
                    self._write_metric_row(writer, results["metadata"], run_id)

            self.logger.info("csv_saved", path=str(csv_file))
            return csv_file

        except Exception as e:
            self.logger.error("csv_save_failed", path=str(csv_file), error=str(e))
            raise

    def _write_metric_row(self, writer, metric, run_id: str):
        """Write a single metric row to CSV"""
        metric_dict = metric.to_dict()
        latencies = metric_dict.get("latency_percentiles", {})

        writer.writerow([
            metric_dict.get("test_name", ""),
            metric_dict.get("file_size_mb", 0),
            metric_dict.get("elapsed_sec", 0),
            metric_dict.get("throughput_mbps", 0),
            metric_dict.get("iops", 0),
            metric_dict.get("operations_count", 0),
            latencies.get("p50", ""),
            latencies.get("p95", ""),
            latencies.get("p99", ""),
            run_id,
        ])

    def save_json(self,
                  results: Dict,
                  system_info: Dict,
                  run_id: str) -> Path:
        """Save complete results including system info to JSON"""
        json_file = Config.RESULTS_DIR / f"full_results_{run_id}.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("saving_json", path=str(json_file))

        try:
            # Convert metrics to dictionaries
            output = {
                "run_id": run_id,
                "system_info": system_info,
                "results": {
                    "sequential_write": [m.to_dict() for m in results["sequential_write"]],
                    "sequential_read": [m.to_dict() for m in results["sequential_read"]],
                    "random_rw": results["random_rw"].to_dict() if results["random_rw"] else None,
                    "metadata": results["metadata"].to_dict() if results["metadata"] else None,
                }
            }

            with open(json_file, "w") as f:
                json.dump(output, f, indent=2)

            self.logger.info("json_saved", path=str(json_file))
            return json_file

        except Exception as e:
            self.logger.error("json_save_failed", path=str(json_file), error=str(e))
            raise

    def generate_graph(self,
                       results: Dict,
                       run_id: str) -> Path:
        """Generate comprehensive benchmark visualization"""
        output_path = Config.GRAPHS_DIR / f"benchmark_chart_{run_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("generating_graph", path=str(output_path))

        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'Filesystem Benchmark Results - {run_id}',
                         fontsize=16, fontweight='bold')

            # 1. Throughput comparison
            self._plot_throughput(ax1, results)

            # 2. IOPS comparison
            self._plot_iops(ax2, results)

            # 3. Latency percentiles
            self._plot_latencies(ax3, results)

            # 4. Time comparison
            self._plot_times(ax4, results)

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info("graph_generated", path=str(output_path))
            return output_path

        except Exception as e:
            self.logger.error("graph_generation_failed",
                              path=str(output_path), error=str(e))
            raise

    def _plot_throughput(self, ax, results):
        """Plot throughput comparison"""
        tests = []
        throughputs = []

        for metric in results["sequential_write"]:
            tests.append(f"Write {metric.to_dict()['file_size_mb'] / 1024:.0f}GB")
            throughputs.append(metric.throughput_mbps)

        for metric in results["sequential_read"]:
            tests.append(f"Read {metric.to_dict()['file_size_mb'] / 1024:.0f}GB")
            throughputs.append(metric.throughput_mbps)

        bars = ax.bar(tests, throughputs, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax.set_ylabel('Throughput (MB/s)', fontsize=11)
        ax.set_title('Sequential I/O Throughput', fontsize=12, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)

    def _plot_iops(self, ax, results):
        """Plot IOPS comparison"""
        tests = []
        iops_values = []

        # Add small file operations
        if results["random_rw"]:
            tests.append("Random R/W")
            iops_values.append(results["random_rw"].iops)

        if results["metadata"]:
            tests.append("Metadata Ops")
            iops_values.append(results["metadata"].iops)

        bars = ax.bar(tests, iops_values, color=['#FFD93D', '#6BCF7F'])
        ax.set_ylabel('IOPS', fontsize=11)
        ax.set_title('Operations Per Second', fontsize=12, fontweight='bold')

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)

    def _plot_latencies(self, ax, results):
        """Plot latency percentiles"""
        all_metrics = []
        all_metrics.extend(results["sequential_write"])
        all_metrics.extend(results["sequential_read"])
        if results["random_rw"]:
            all_metrics.append(results["random_rw"])

        test_names = []
        p50_values = []
        p95_values = []
        p99_values = []

        for metric in all_metrics:
            if metric.latency_percentiles:
                test_names.append(metric.test_name.replace("Sequential ", ""))
                p50_values.append(metric.latency_percentiles.get("p50", 0) * 1000)  # Convert to ms
                p95_values.append(metric.latency_percentiles.get("p95", 0) * 1000)
                p99_values.append(metric.latency_percentiles.get("p99", 0) * 1000)

        x = np.arange(len(test_names))
        width = 0.25

        ax.bar(x - width, p50_values, width, label='P50', color='#95E1D3')
        ax.bar(x, p95_values, width, label='P95', color='#F38181')
        ax.bar(x + width, p99_values, width, label='P99', color='#AA96DA')

        ax.set_ylabel('Latency (ms)', fontsize=11)
        ax.set_title('Latency Percentiles', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(test_names, rotation=45, ha='right')
        ax.legend()

    def _plot_times(self, ax, results):
        """Plot execution time comparison"""
        tests = []
        times = []

        for metric in results["sequential_write"]:
            tests.append(f"Write {metric.to_dict()['file_size_mb'] / 1024:.0f}GB")
            times.append(metric.elapsed_sec)

        for metric in results["sequential_read"]:
            tests.append(f"Read {metric.to_dict()['file_size_mb'] / 1024:.0f}GB")
            times.append(metric.elapsed_sec)

        if results["random_rw"]:
            tests.append("Random R/W")
            times.append(results["random_rw"].elapsed_sec)

        if results["metadata"]:
            tests.append("Metadata")
            times.append(results["metadata"].elapsed_sec)

        bars = ax.bar(tests, times, color='skyblue', edgecolor='navy', alpha=0.7)
        ax.set_ylabel('Time (seconds)', fontsize=11)
        ax.set_title('Execution Time', fontsize=12, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}s',
                    ha='center', va='bottom', fontsize=8)