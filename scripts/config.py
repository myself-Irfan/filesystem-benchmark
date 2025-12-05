import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()


def get_env_or_raise(key: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        raise ValueError(f"Environment variable '{key}' is required but not set.")
    return value.strip()


class Config:
    BASE_DIR = Path(get_env_or_raise("BASE_DIR"))
    LARGE_FILES_DIR = BASE_DIR / get_env_or_raise("LARGE_FILES_SUBDIR")
    SMALL_FILES_DIR = BASE_DIR / get_env_or_raise("SMALL_FILES_SUBDIR")

    RESULTS_BASE_DIR = Path(get_env_or_raise("RESULTS_BASE_DIR"))
    RESULTS_DIR = RESULTS_BASE_DIR / get_env_or_raise("RESULTS_SUBDIR")
    GRAPHS_DIR = RESULTS_BASE_DIR / get_env_or_raise("GRAPHS_SUBDIR")
    LOG_DIR = RESULTS_BASE_DIR / get_env_or_raise("LOG_DIR")

    @staticmethod
    def get_large_file_sizes_gb() -> List[int]:
        sizes_str = get_env_or_raise("LARGE_FILE_SIZES_GB")  # comma-separated
        return [int(s.strip()) for s in sizes_str.split(",")]

    SMALL_FILE_COUNT = int(get_env_or_raise("SMALL_FILE_COUNT"))

    @staticmethod
    def get_small_file_size_range_kb() -> tuple:
        range_str = get_env_or_raise("SMALL_FILE_SIZE_RANGE_KB")  # format: min,max
        min_kb, max_kb = range_str.split(",")
        return int(min_kb.strip()), int(max_kb.strip())

    SEQUENTIAL_WRITE_SIZE_MB = int(get_env_or_raise("SEQUENTIAL_WRITE_SIZE_MB"))
    RANDOM_APPEND_SIZE_KB = int(get_env_or_raise("RANDOM_APPEND_SIZE_KB"))
    METADATA_OPERATIONS_COUNT = int(get_env_or_raise("METADATA_OPERATIONS_COUNT"))
    READ_BUFFER_SIZE = int(get_env_or_raise("READ_BUFFER_SIZE"))

    @staticmethod
    def get_latency_percentiles() -> List[float]:
        percentiles_str = get_env_or_raise("LATENCY_PERCENTILES")  # comma-separated
        return [float(p.strip()) for p in percentiles_str.split(",")]

    LATENCY_SAMPLES = int(get_env_or_raise("LATENCY_SAMPLES"))
