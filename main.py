import sys
import logging
from pathlib import Path
from datetime import datetime
import structlog

from scripts.generate_files import FileGenerator
from scripts.benchmarks import BenchmarkRunner
from scripts.parser import ResultsParser
from scripts.system_info import SystemInfo
from scripts.config import Config


def setup_logging(run_id: str) -> structlog.BoundLogger:
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{run_id}.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    ))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    ))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )

    structlog.configure(
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

def log_summary(results: dict, system_info: dict, logger: structlog.BoundLogger):
    logger.info("BENCHMARK SUMMARY")

    logger.info("SEQUENTIAL WRITE:")
    for metric in results["sequential_write"]:
        m = metric.to_dict()
        logger.info(f"{m['test_name']}:", throughput_mbps=f"{m['throughput_mbps']:.2f}", iops=f"{m['iops']:.2f}")
        if m['latency_percentiles']:
            logger.info(
                "Latency percentiles (ms)",
                    p50=f"{m['latency_percentiles'].get('p50', 0) * 1000:.2f}",
                    p95=f"{m['latency_percentiles'].get('p95', 0) * 1000:.2f}",
                    p99=f"{m['latency_percentiles'].get('p99', 0) * 1000:.2f}"
                    )

    logger.info("SEQUENTIAL READ:")
    for metric in results["sequential_read"]:
        m = metric.to_dict()
        logger.info(f"{m['test_name']}:",
                    throughput_mbps=f"{m['throughput_mbps']:.2f}",
                    iops=f"{m['iops']:.2f}")
        if m['latency_percentiles']:
            logger.info("Latency percentiles (ms)",
                        p50=f"{m['latency_percentiles'].get('p50', 0) * 1000:.2f}",
                        p95=f"{m['latency_percentiles'].get('p95', 0) * 1000:.2f}",
                        p99=f"{m['latency_percentiles'].get('p99', 0) * 1000:.2f}")

    if results["random_rw"]:
        m = results["random_rw"].to_dict()
        logger.info("RANDOM READ/WRITE:",
                    operations=m['operations_count'],
                    iops=f"{m['iops']:.2f}",
                    elapsed_sec=f"{m['elapsed_sec']:.2f}")
        if m['latency_percentiles']:
            logger.info("    Latency percentiles (ms)",
                        p50=f"{m['latency_percentiles'].get('p50', 0) * 1000:.2f}",
                        p95=f"{m['latency_percentiles'].get('p95', 0) * 1000:.2f}",
                        p99=f"{m['latency_percentiles'].get('p99', 0) * 1000:.2f}")

    if results["metadata"]:
        m = results["metadata"].to_dict()
        logger.info("METADATA OPERATIONS:",
                    operations=m['operations_count'],
                    iops=f"{m['iops']:.2f}",
                    elapsed_sec=f"{m['elapsed_sec']:.2f}")

    logger.info("=" * 70)

def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logging(run_id)

    try:
        logger.info("benchmark_suite_started", run_id=run_id)
        ensure_directories()

        logger.info("step_started", step=0, description="Collecting system information")
        sys_info = SystemInfo(logger)
        system_info = sys_info.collect_all(Config.BASE_DIR)
        logger.info("system_information", info=sys_info.format_for_display(system_info))
        logger.info("step_completed", step=0)

        logger.info("step_started", step=1, description="Generating test files")
        file_gen = FileGenerator(logger)
        file_gen.generate_large_files()
        file_gen.generate_small_files()
        logger.info("step_completed", step=1)

        logger.info("step_started", step=2, description="Running benchmarks")
        runner = BenchmarkRunner(logger)
        results = runner.run_all_benchmarks()
        logger.info("step_completed", step=2)

        logger.info("step_started", step=3, description="Saving results")
        parser = ResultsParser(logger)
        csv_path = parser.save_csv(results, system_info, run_id)
        json_path = parser.save_json(results, system_info, run_id)
        logger.info("step_completed", step=3, csv_path=csv_path, json_path=json_path)

        logger.info("step_started", step=4, description="Generating graphs")
        graph_path = parser.generate_graph(results, run_id)
        logger.info("step_completed", step=4, graph_path=graph_path)

        log_summary(results, system_info, logger)

        logger.info("benchmark_suite_completed", run_id=run_id, csv_path=str(csv_path), json_path=str(json_path), graph_path=str(graph_path))
        logger.info("results_saved", csv=str(csv_path), json=str(json_path), graph=str(graph_path))

    except Exception as e:
        logger.exception("benchmark_suite_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()