import sys
import logging
from pathlib import Path
from datetime import datetime
import structlog

from scripts.generate_files import FileGenerator
from scripts.benchmarks import BenchmarkRunner
from scripts.parser import ResultsParser
from scripts.config import Config


def setup_logging(run_id: str) -> structlog.BoundLogger:
    log_dir = Path(Config.LOG_DIR) / run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "benchmark.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        format="%(message)s"
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger()
    logger.info("logging_initialized", log_file=str(log_file), run_id=run_id)
    return logger


def ensure_directories():
    dirs = [
        Config.LARGE_FILES_DIR,
        Config.SMALL_FILES_DIR,
        Config.RESULTS_DIR,
        Config.GRAPHS_DIR,
        Config.LOG_DIR,
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logging(run_id)

    try:
        logger.info("benchmark_suite_started", run_id=run_id)
        ensure_directories()

        logger.info("step_started", step=1, description="Generating test files")
        file_gen = FileGenerator(logger)
        file_gen.generate_large_files()
        file_gen.generate_small_files()
        logger.info("step_completed", step=1)

        logger.info("step_started", step=2, description="Running benchmarks")
        runner = BenchmarkRunner(logger)
        results = runner.run_all_benchmarks()
        logger.info("step_completed", step=2, total_tests=len(results))

        logger.info("step_started", step=3, description="Saving results")
        parser = ResultsParser(logger)
        csv_path = parser.save_csv(results, run_id)
        logger.info("step_completed", step=3, csv_path=csv_path)

        logger.info("step_started", step=4, description="Generating graphs")
        graph_path = parser.generate_graph(results, run_id)
        logger.info("step_completed", step=4, graph_path=graph_path)

        logger.info("benchmark_suite_completed", run_id=run_id, results=results, csv_path=csv_path, graph_path=graph_path)

    except Exception as e:
        logger.exception("benchmark_suite_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()