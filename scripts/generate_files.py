import os
import random
from pathlib import Path
from typing import Optional
import structlog

from scripts.config import Config


class FileGenerator:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()

    def generate_large_files(self, output_dir: Optional[Path] = None) -> None:
        output_dir = output_dir or Config.LARGE_FILES_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("generating_large_files", sizes_gb=Config.LARGE_FILE_SIZES_GB, output_dir=str(output_dir))

        for size_gb in Config.LARGE_FILE_SIZES_GB:
            file_path = output_dir / f"file_{size_gb}GB.bin"

            if file_path.exists():
                self.logger.info("large_file_exists_skipping", path=str(file_path), size_gb=size_gb)
                continue

            try:
                size_bytes = size_gb * 1024 * 1024 * 1024
                self.logger.info("creating_large_file",
                                 path=str(file_path),
                                 size_gb=size_gb)

                with open(file_path, "wb") as f:
                    chunk_size = 100 * 1024 * 1024
                    chunks = size_bytes // chunk_size

                    for i in range(chunks):
                        f.write(os.urandom(chunk_size))
                        if (i + 1) % 10 == 0:
                            self.logger.debug("large_file_progress",
                                              path=str(file_path),
                                              progress_pct=(i + 1) / chunks * 100)

                self.logger.info("large_file_created",
                                 path=str(file_path),
                                 size_gb=size_gb)

            except Exception as e:
                self.logger.error("large_file_creation_failed",
                                  path=str(file_path),
                                  error=str(e))
                raise

    def generate_small_files(self, output_dir: Optional[Path] = None, count: Optional[int] = None) -> None:
        output_dir = output_dir or Config.SMALL_FILES_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        count = count or Config.SMALL_FILE_COUNT
        min_kb, max_kb = Config.SMALL_FILE_SIZE_RANGE_KB

        self.logger.info("generating_small_files", count=count, size_range_kb=(min_kb, max_kb), output_dir=str(output_dir))

        try:
            for i in range(count):
                size_kb = random.randint(min_kb, max_kb)
                file_path = output_dir / f"file_{i}.txt"

                with open(file_path, "wb") as f:
                    f.write(os.urandom(size_kb * 1024))

                if (i + 1) % 1000 == 0:
                    self.logger.debug("small_files_progress",
                                      created=i + 1,
                                      total=count)

            self.logger.info("small_files_created",
                             count=count,
                             output_dir=str(output_dir))

        except Exception as e:
            self.logger.error("small_files_creation_failed",
                              error=str(e))
            raise