# Filesystem Benchmark Suite

A comprehensive filesystem performance testing tool with structured logging, detailed metrics, and visualization capabilities.

## 🚀 Features

- **Sequential I/O Testing**: Measure read/write performance on large files (1GB, 2GB, 5GB)
- **Random I/O Testing**: Test performance with thousands of small files
- **Metadata Operations**: Benchmark file creation, permission changes, and deletion
- **Structured Logging**: Detailed logs using structlog with real-time console output and file logging
- **Results Visualization**: Automatic CSV export and professional graph generation
- **Per-Run Tracking**: Each benchmark run gets its own timestamped directory for logs and results

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package manager)

## 🔧 Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🎯 Quick Start

Run the complete benchmark suite:

```bash
python main.py
```

The script will:
1. Generate test files (large and small)
2. Run all benchmark tests
3. Save results to CSV
4. Generate visualization graphs
5. Log everything to console and file

## 📁 Project Structure

```
filesystem-benchmark/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore            # Git ignore rules
├── scripts/                  # Source package
│   ├── config.py         # Configuration settings
│   ├── benchmarks.py     # Benchmark implementations
│   ├── generate_files.py # Test file generation
│   ├── metadata.py       # Metadata operations
│   └── parser.py         # Results parsing and visualization
├── data/                 # Test files (git-ignored)
│   ├── large/            # Large test files (1GB+)
│   └── small/            # Small test files (1-100KB)
└── results/              # Benchmark outputs (git-ignored)
    ├── raw/              # CSV results per run
    ├── graphs/           # PNG visualizations per run
    └── logs/             # Structured logs per run
        └── YYYYMMDD_HHMMSS/
            └── benchmark.log
```

## 🧪 Benchmark Tests

### 1. Sequential Write
- Writes a 1GB file sequentially
- Measures write throughput (MB/s)

### 2. Sequential Read
- Reads a 1GB file sequentially
- Measures read throughput (MB/s)

### 3. Random Read/Write Small Files
- Reads 5,000 small files (1-100KB each)
- Appends 1KB to each file
- Measures operations per second

### 4. Metadata Operations
- Creates 1,000 files
- Changes permissions on all files
- Deletes all files
- Measures operations per second

## ⚙️ Configuration

Customize benchmark parameters by editing `src/config.py`:

```python
class Config:
    # File generation settings
    LARGE_FILE_SIZES_GB = [1, 2, 5]
    SMALL_FILE_COUNT = 5000
    SMALL_FILE_SIZE_RANGE_KB = (1, 100)
    
    # Benchmark settings
    SEQUENTIAL_WRITE_SIZE_MB = 1024
    METADATA_OPERATIONS_COUNT = 1000
    
    # Buffer sizes
    READ_BUFFER_SIZE = 1024 * 1024  # 1MB
```

## 📊 Output Files

Each benchmark run generates timestamped outputs:

### Console Output
Real-time progress with colored, structured logs:
```
2024-12-03T10:30:45.123456Z [info     ] benchmark_suite_started run_id=20241203_103045
2024-12-03T10:30:45.234567Z [info     ] step_started description=Generating test files step=1
...
```

### Log File
`results/logs/YYYYMMDD_HHMMSS/benchmark.log`
- Complete structured log of all operations
- Includes timing, throughput, and performance metrics

### CSV Results
`results/raw/metrics_YYYYMMDD_HHMMSS.csv`
```csv
Test,Time_sec,Run_ID
Sequential Write,12.34,20241203_103045
Sequential Read,8.56,20241203_103045
...
```

### Visualization
`results/graphs/benchmark_chart_YYYYMMDD_HHMMSS.png`
- Bar chart comparing all test results
- Value labels showing exact timings
- Professional styling with grid

## 🔍 Understanding Results

**Lower times are better** for all tests.

- **Sequential I/O**: Tests raw disk read/write speed
  - Good: < 10 seconds for 1GB
  - Excellent: < 5 seconds for 1GB

- **Random I/O**: Tests performance with many small files
  - Depends heavily on filesystem and storage type
  - SSD performs significantly better than HDD

- **Metadata Operations**: Tests filesystem overhead
  - Good: < 2 seconds for 1000 operations
  - Excellent: < 1 second for 1000 operations

## 🛠️ Troubleshooting

### Large File Generation Takes Too Long
- This is normal for multi-GB files
- Files are only generated once and reused
- Check if files already exist in `data/large/`

### Out of Disk Space
- Large files require significant space (8GB+ total)
- Reduce `LARGE_FILE_SIZES_GB` in config.py
- Delete test files in `data/` when done

### Permission Errors
- Ensure write permissions in project directory
- On Unix/Linux, check folder permissions: `chmod 755 .`

## 📝 Example Session

```bash
$ python main.py

2024-12-03T10:30:45.123456Z [info     ] benchmark_suite_started run_id=20241203_103045
2024-12-03T10:30:45.234567Z [info     ] step_started description=Generating test files step=1
2024-12-03T10:30:45.345678Z [info     ] generating_large_files output_dir=data/large sizes_gb=[1, 2, 5]
2024-12-03T10:30:45.456789Z [info     ] large_file_exists_skipping path=data/large/file_1GB.bin size_gb=1
...
2024-12-03T10:35:20.123456Z [info     ] benchmark_completed elapsed_sec=12.34 test=sequential_write throughput_mbps=82.97
...
2024-12-03T10:40:15.789012Z [info     ] all_benchmarks_completed
2024-12-03T10:40:16.890123Z [info     ] benchmark_suite_completed

All steps completed! Check results/ for outputs.
```

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📄 License

This project is open source and available for educational and testing purposes.

## ⚠️ Warning

This tool writes and reads large amounts of data. Ensure you have:
- Sufficient disk space (10GB+ recommended)
- Permission to perform I/O benchmarks
- Understanding that results will vary by hardware

## 🔗 Related Tools

- [fio](https://github.com/axboe/fio) - Flexible I/O Tester
- [ioping](https://github.com/koct9i/ioping) - Simple disk I/O latency monitoring tool
- [dd](https://www.gnu.org/software/coreutils/manual/html_node/dd-invocation.html) - Convert and copy a file