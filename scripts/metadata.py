"""
Metadata operations benchmarking.
"""
import os
import time
from pathlib import Path
from typing import Optional
import structlog

from scripts.config import Config


class MetadataOperations:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()

    def run_metadata_tests(self,
                           dir_path: Optional[Path] = None,
                           count: Optional[int] = None) -> float:
        dir_path = dir_path or Config.SMALL_FILES_DIR
        dir_path = Path(dir_path)
        count = count or Config.METADATA_OPERATIONS_COUNT

        self.logger.info("benchmark_started",
                         test="metadata_operations",
                         dir_path=str(dir_path),
                         file_count=count)

        file_paths = []
        try:
            start = time.time()

            self.logger.debug("metadata_phase_started", phase="create")
            for i in range(count):
                file_path = dir_path / f"meta_{i}.txt"
                file_path.touch()
                file_paths.append(file_path)

            self.logger.debug("metadata_phase_started", phase="chmod")
            for file_path in file_paths:
                os.chmod(file_path, 0o644)

            self.logger.debug("metadata_phase_started", phase="delete")
            for file_path in file_paths:
                file_path.unlink()

            elapsed = time.time() - start

            total_ops = count * 3
            ops_per_sec = total_ops / elapsed

            self.logger.info("benchmark_completed",
                             test="metadata_operations",
                             elapsed_sec=elapsed,
                             file_count=count,
                             total_operations=total_ops,
                             ops_per_sec=ops_per_sec)
            return elapsed

        except Exception as e:
            self.logger.error("benchmark_failed",
                              test="metadata_operations",
                              error=str(e))
            for file_path in file_paths:
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception:
                    pass
            raise