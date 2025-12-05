import os
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import structlog

from scripts.config import Config
from scripts.metadata import MetadataOperations


class BenchmarkMetrics:
    """Container for benchmark metrics"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.elapsed_sec = 0.0
        self.throughput_mbps = 0.0
        self.iops = 0.0
        self.latency_percentiles = {}
        self.file_size_mb = 0.0
        self.operations_count = 0

    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "elapsed_sec": round(self.elapsed_sec, 3),
            "throughput_mbps": round(self.throughput_mbps, 2),
            "iops": round(self.iops, 2),
            "latency_percentiles": {k: round(v, 4) for k, v in self.latency_percentiles.items()},
            "file_size_mb": round(self.file_size_mb, 2),
            "operations_count": self.operations_count,
        }


class BenchmarkRunner:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()
        self.metadata_ops = MetadataOperations(logger)

    def _calculate_percentiles(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency percentiles"""
        if not latencies:
            return {}

        percentiles = Config.get_latency_percentiles()
        result = {}
        for p in percentiles:
            result[f"p{int(p)}"] = np.percentile(latencies, p)
        return result

    def sequential_write_multi_size(self) -> List[BenchmarkMetrics]:
        """Test sequential write with multiple file sizes"""
        results = []
        file_sizes = Config.get_large_file_sizes_gb()

        for size_gb in file_sizes:
            metrics = self._sequential_write_single(size_gb)
            results.append(metrics)

        return results

    def _sequential_write_single(self, size_gb: int) -> BenchmarkMetrics:
        """Sequential write for a specific file size"""
        file_path = Config.LARGE_FILES_DIR / f"file_{size_gb}GB.bin"
        size_mb = size_gb * 1024

        metrics = BenchmarkMetrics(f"Sequential Write {size_gb}GB")
        metrics.file_size_mb = size_mb

        self.logger.info("benchmark_started",
                         test=metrics.test_name,
                         file_path=str(file_path),
                         size_mb=size_mb)

        try:
            # Measure per-chunk latency for first N chunks
            chunk_size_mb = 100
            chunk_size_bytes = chunk_size_mb * 1024 * 1024
            total_chunks = size_mb // chunk_size_mb
            sample_size = min(Config.LATENCY_SAMPLES, total_chunks)

            latencies = []
            overall_start = time.time()

            with open(file_path, "wb") as f:
                for i in range(total_chunks):
                    chunk_start = time.time()
                    f.write(os.urandom(chunk_size_bytes))
                    chunk_elapsed = time.time() - chunk_start

                    if i < sample_size:
                        latencies.append(chunk_elapsed)

            metrics.elapsed_sec = time.time() - overall_start
            metrics.throughput_mbps = size_mb / metrics.elapsed_sec
            metrics.operations_count = total_chunks
            metrics.iops = total_chunks / metrics.elapsed_sec
            metrics.latency_percentiles = self._calculate_percentiles(latencies)

            self.logger.info("benchmark_completed",
                             test=metrics.test_name,
                             metrics=metrics.to_dict())
            return metrics

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test=metrics.test_name,
                              error=str(e))
            raise

    def sequential_read_multi_size(self) -> List[BenchmarkMetrics]:
        """Test sequential read with multiple file sizes"""
        results = []
        file_sizes = Config.get_large_file_sizes_gb()

        for size_gb in file_sizes:
            metrics = self._sequential_read_single(size_gb)
            results.append(metrics)

        return results

    def _sequential_read_single(self, size_gb: int) -> BenchmarkMetrics:
        """Sequential read for a specific file size"""
        file_path = Config.LARGE_FILES_DIR / f"file_{size_gb}GB.bin"

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")

        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

        metrics = BenchmarkMetrics(f"Sequential Read {size_gb}GB")
        metrics.file_size_mb = file_size_mb

        self.logger.info("benchmark_started",
                         test=metrics.test_name,
                         file_path=str(file_path),
                         file_size_mb=file_size_mb)

        try:
            buffer_size = Config.READ_BUFFER_SIZE
            sample_size = Config.LATENCY_SAMPLES

            latencies = []
            operations = 0
            overall_start = time.time()

            with open(file_path, "rb") as f:
                while chunk := f.read(buffer_size):
                    operations += 1

                    # Sample latency for first N operations
                    if operations <= sample_size:
                        chunk_start = time.time()
                        _ = len(chunk)  # Simulate minimal processing
                        chunk_elapsed = time.time() - chunk_start
                        latencies.append(chunk_elapsed)

            metrics.elapsed_sec = time.time() - overall_start
            metrics.throughput_mbps = file_size_mb / metrics.elapsed_sec
            metrics.operations_count = operations
            metrics.iops = operations / metrics.elapsed_sec
            metrics.latency_percentiles = self._calculate_percentiles(latencies)

            self.logger.info("benchmark_completed",
                             test=metrics.test_name,
                             metrics=metrics.to_dict())
            return metrics

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test=metrics.test_name,
                              error=str(e))
            raise

    def random_file_read_write(self, dir_path: Optional[Path] = None) -> BenchmarkMetrics:
        """Random file read/write with enhanced metrics"""
        dir_path = dir_path or Config.SMALL_FILES_DIR
        dir_path = Path(dir_path)

        files = list(dir_path.glob("file_*.txt"))
        if not files:
            raise FileNotFoundError(f"No test files found in {dir_path}")

        metrics = BenchmarkMetrics("Random Read/Write Small Files")

        self.logger.info("benchmark_started",
                         test=metrics.test_name,
                         dir_path=str(dir_path),
                         file_count=len(files))

        try:
            sample_size = min(Config.LATENCY_SAMPLES, len(files))
            latencies = []

            overall_start = time.time()

            # Read phase with latency sampling
            for i, file_path in enumerate(files):
                op_start = time.time()
                with open(file_path, "rb") as f:
                    f.read()
                op_elapsed = time.time() - op_start

                if i < sample_size:
                    latencies.append(op_elapsed)

            # Write phase with latency sampling
            append_size = Config.RANDOM_APPEND_SIZE_KB * 1024
            for i, file_path in enumerate(files):
                op_start = time.time()
                with open(file_path, "ab") as f:
                    f.write(os.urandom(append_size))
                op_elapsed = time.time() - op_start

                if i < sample_size:
                    latencies.append(op_elapsed)

            metrics.elapsed_sec = time.time() - overall_start
            metrics.operations_count = len(files) * 2  # read + write per file
            metrics.iops = metrics.operations_count / metrics.elapsed_sec
            metrics.latency_percentiles = self._calculate_percentiles(latencies)

            self.logger.info("benchmark_completed",
                             test=metrics.test_name,
                             metrics=metrics.to_dict())
            return metrics

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test=metrics.test_name,
                              error=str(e))
            raise

    def run_all_benchmarks(self) -> Dict[str, any]:
        """Run all benchmarks and return comprehensive results"""
        self.logger.info("running_all_benchmarks")

        results = {
            "sequential_write": [],
            "sequential_read": [],
            "random_rw": None,
            "metadata": None,
        }

        try:
            # Multi-size sequential tests
            self.logger.info("phase_started", phase="sequential_write")
            results["sequential_write"] = self.sequential_write_multi_size()

            self.logger.info("phase_started", phase="sequential_read")
            results["sequential_read"] = self.sequential_read_multi_size()

            # Small file operations
            self.logger.info("phase_started", phase="random_rw")
            results["random_rw"] = self.random_file_read_write()

            # Metadata operations
            self.logger.info("phase_started", phase="metadata")
            metadata_metrics = BenchmarkMetrics("Metadata Operations")
            metadata_metrics.elapsed_sec = self.metadata_ops.run_metadata_tests()
            metadata_metrics.operations_count = Config.METADATA_OPERATIONS_COUNT * 3
            metadata_metrics.iops = metadata_metrics.operations_count / metadata_metrics.elapsed_sec
            results["metadata"] = metadata_metrics

            self.logger.info("all_benchmarks_completed")
            return results

        except Exception as e:
            self.logger.error("benchmarks_failed", error=str(e))
            raise