"""
Benchmark implementations for filesystem performance testing.
"""
import os
import time
from pathlib import Path
from typing import Dict, Optional
import structlog

from scripts.config import Config
from scripts.metadata import MetadataOperations


class BenchmarkRunner:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()
        self.metadata_ops = MetadataOperations(logger)

    def sequential_write(self,
                         file_path: Optional[Path] = None,
                         size_mb: Optional[int] = None) -> float:
        file_path = file_path or (Config.LARGE_FILES_DIR / "file_1GB.bin")
        size_mb = size_mb or Config.SEQUENTIAL_WRITE_SIZE_MB

        self.logger.info("benchmark_started",
                         test="sequential_write",
                         file_path=str(file_path),
                         size_mb=size_mb)

        try:
            start = time.time()
            with open(file_path, "wb") as f:
                f.write(os.urandom(size_mb * 1024 * 1024))
            elapsed = time.time() - start

            throughput_mbps = size_mb / elapsed
            self.logger.info("benchmark_completed",
                             test="sequential_write",
                             elapsed_sec=elapsed,
                             throughput_mbps=throughput_mbps)
            return elapsed

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test="sequential_write",
                              error=str(e))
            raise

    def sequential_read(self, file_path: Optional[Path] = None) -> float:
        file_path = file_path or (Config.LARGE_FILES_DIR / "file_1GB.bin")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")

        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        self.logger.info("benchmark_started",
                         test="sequential_read",
                         file_path=str(file_path),
                         file_size_mb=file_size_mb)

        try:
            start = time.time()
            with open(file_path, "rb") as f:
                while chunk := f.read(Config.READ_BUFFER_SIZE):
                    pass
            elapsed = time.time() - start

            throughput_mbps = file_size_mb / elapsed
            self.logger.info("benchmark_completed",
                             test="sequential_read",
                             elapsed_sec=elapsed,
                             throughput_mbps=throughput_mbps)
            return elapsed

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test="sequential_read",
                              error=str(e))
            raise

    def random_file_read_write(self, dir_path: Optional[Path] = None) -> float:
        dir_path = dir_path or Config.SMALL_FILES_DIR
        dir_path = Path(dir_path)

        files = list(dir_path.glob("file_*.txt"))
        if not files:
            raise FileNotFoundError(f"No test files found in {dir_path}")

        self.logger.info("benchmark_started",
                         test="random_file_read_write",
                         dir_path=str(dir_path),
                         file_count=len(files))

        try:
            start = time.time()

            for file_path in files:
                with open(file_path, "rb") as f:
                    f.read()

            append_size = Config.RANDOM_APPEND_SIZE_KB * 1024
            for file_path in files:
                with open(file_path, "ab") as f:
                    f.write(os.urandom(append_size))

            elapsed = time.time() - start

            ops_per_sec = (len(files) * 2) / elapsed  # 2 ops per file
            self.logger.info("benchmark_completed",
                             test="random_file_read_write",
                             elapsed_sec=elapsed,
                             file_count=len(files),
                             ops_per_sec=ops_per_sec)
            return elapsed

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test="random_file_read_write",
                              error=str(e))
            raise

    def run_all_benchmarks(self) -> Dict[str, float]:
        self.logger.info("running_all_benchmarks")

        results = {}

        try:
            results["Sequential Write"] = self.sequential_write()
            results["Sequential Read"] = self.sequential_read()
            results["Random Read/Write Small Files"] = self.random_file_read_write()
            results["Metadata Operations"] = self.metadata_ops.run_metadata_tests()

            self.logger.info("all_benchmarks_completed", results=results)
            return results

        except Exception as e:
            self.logger.error("benchmarks_failed", error=str(e))
            raise