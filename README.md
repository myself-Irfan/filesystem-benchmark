# Filesystem Performance Benchmark Suite

A comprehensive Python tool for benchmarking filesystem performance with detailed metrics including throughput, IOPS, and latency percentiles.

## Features

✅ **Multi-size Testing** - Test sequential operations on multiple file sizes (1GB, 2GB, 5GB)  
✅ **System Information Capture** - Records CPU, RAM, disk type, OS details  
✅ **Advanced Metrics** - Throughput (MB/s), IOPS, latency percentiles (P50, P95, P99)  
✅ **Configurable via .env** - No hardcoded values, easy customization  
✅ **Comprehensive Reports** - CSV data + JSON with system info + visual graphs  
✅ **Structured Logging** - Detailed logs for debugging and analysis  

## Installation

```bash
# Clone or download the project
cd filesystem-benchmark

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env to customize settings
```

## Configuration

Edit `.env` to customize benchmark parameters:

```bash
# Test all large file sizes or just 1GB
TEST_ALL_LARGE_FILES=true

# File sizes to generate and test (comma-separated, in GB)
LARGE_FILE_SIZES_GB=1,2,5

# Number of small files for random I/O testing
SMALL_FILE_COUNT=5000

# Latency percentiles to calculate
LATENCY_PERCENTILES=50,95,99

# Number of operations to sample for latency stats
LATENCY_SAMPLES=100
```

## Usage

```bash
# Run full benchmark suite
python main.py
```

The tool will:
1. Collect system information (CPU, RAM, disk, OS)
2. Generate test files if they don't exist
3. Run all benchmarks with progress logging
4. Save results to CSV and JSON
5. Generate performance visualization graphs
6. Display summary in console

## Benchmark Tests

### 1. Sequential Write (Multi-size)
- Writes large files (1GB, 2GB, 5GB based on config)
- Measures throughput (MB/s), IOPS, latency percentiles
- Tests sustained write performance

### 2. Sequential Read (Multi-size)
- Reads large files in chunks
- Measures throughput (MB/s), IOPS, latency percentiles
- Tests sustained read performance

### 3. Random Read/Write Small Files
- Reads 5,000 small files (1-100 KB each)
- Appends data to each file
- Measures IOPS and latency
- Tests small file handling

### 4. Metadata Operations
- Creates 1,000 files
- Changes permissions
- Deletes all files
- Measures metadata IOPS

## Output Files

Results are saved in `results/` directory:

```
results/
├── raw/
│   ├── metrics_20241205_143022.csv      # Detailed metrics
│   └── full_results_20241205_143022.json # Complete data + system info
├── graphs/
│   └── benchmark_chart_20241205_143022.png # Visual charts
└── logs/
    └── 20241205_143022/
        └── benchmark.log                 # Detailed execution log
```

### CSV Columns
- Test_Name
- File_Size_MB
- Elapsed_Sec
- Throughput_MBps
- IOPS
- Operations
- Latency_P50, Latency_P95, Latency_P99
- Run_ID

### JSON Structure
```json
{
  "run_id": "20241205_143022",
  "system_info": {
    "cpu": {...},
    "memory": {...},
    "disk": {...},
    "os": {...}
  },
  "results": {
    "sequential_write": [...],
    "sequential_read": [...],
    "random_rw": {...},
    "metadata": {...}
  }
}
```

## Interpreting Results

### Throughput (MB/s)
- Higher is better
- Measures data transfer rate
- Important for large file operations

### IOPS (Operations/Second)
- Higher is better
- Measures number of I/O operations
- Critical for databases and random access

### Latency Percentiles
- Lower is better
- P50 (median): typical performance
- P95: 95% of operations complete within this time
- P99: worst-case performance (excluding top 1%)

## Project Structure

```
filesystem-benchmark/
├── main.py                  # Main orchestrator
├── scripts/
│   ├── config.py           # Configuration loader
│   ├── benchmarks.py       # Benchmark implementations
│   ├── generate_files.py   # Test file generator
│   ├── metadata.py         # Metadata operations
│   ├── parser.py           # Results parser & visualizer
│   └── system_info.py      # System information collector
├── .env.example            # Example configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Advanced Usage

### Test Only 1GB Files (Faster)
```bash
# In .env
TEST_ALL_LARGE_FILES=false
```

### Adjust Latency Sampling
```bash
# In .env
LATENCY_SAMPLES=50  # Fewer samples = faster, less accurate
LATENCY_PERCENTILES=50,90,95,99  # Add more percentiles
```

### Change File Sizes
```bash
# In .env
LARGE_FILE_SIZES_GB=1,4,8  # Test different sizes
SMALL_FILE_COUNT=10000     # More small files
```

## Requirements

- Python 3.8+
- Linux, macOS, or Windows
- Sufficient disk space for test files
- Write permissions in working directory

## Troubleshooting

**Issue**: Out of memory during large file generation  
**Solution**: Large files are written in 100MB chunks, but very large sizes (10GB+) may need more RAM. Reduce file sizes in .env.

**Issue**: Permission denied errors  
**Solution**: Ensure write permissions in the working directory. On Linux, check with `ls -la`.

**Issue**: Slow benchmark execution  
**Solution**: 
- Set `TEST_ALL_LARGE_FILES=false` to only test 1GB
- Reduce `SMALL_FILE_COUNT` 
- Reduce `LATENCY_SAMPLES`

## Performance Expectations

Typical results on modern hardware:

| Operation | SSD | HDD |
|-----------|-----|-----|
| Sequential Write | 500-3000 MB/s | 100-200 MB/s |
| Sequential Read | 500-3500 MB/s | 100-200 MB/s |
| Random IOPS | 10,000-50,000 | 100-200 |
| Metadata IOPS | 5,000-20,000 | 50-150 |

## License

MIT License - Feel free to use and modify.

## Contributing

Contributions welcome! Please test thoroughly before submitting PRs.