import platform
import psutil
import shutil
from pathlib import Path
from typing import Dict, Optional
import structlog


class SystemInfo:
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger()

    def get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information"""
        return {
            "processor": platform.processor() or "Unknown",
            "architecture": platform.machine(),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
        }

    def get_memory_info(self) -> Dict[str, str]:
        """Get memory information"""
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_percent": mem.percent,
        }

    def get_disk_info(self, path: Path) -> Dict[str, str]:
        """Get disk information for the benchmark path"""
        try:
            usage = shutil.disk_usage(path)
            partition = None

            # Try to find the partition
            for part in psutil.disk_partitions():
                if str(path).startswith(part.mountpoint):
                    partition = part
                    break

            info = {
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "used_percent": round((usage.used / usage.total) * 100, 2),
            }

            if partition:
                info["filesystem_type"] = partition.fstype
                info["mount_point"] = partition.mountpoint
                info["device"] = partition.device

            return info
        except Exception as e:
            self.logger.warning("disk_info_failed", error=str(e))
            return {"error": str(e)}

    def get_os_info(self) -> Dict[str, str]:
        """Get operating system information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
        }

    def get_python_info(self) -> Dict[str, str]:
        """Get Python runtime information"""
        return {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        }

    def collect_all(self, benchmark_path: Path) -> Dict[str, Dict]:
        """Collect all system information"""
        self.logger.info("collecting_system_info")

        info = {
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(benchmark_path),
            "os": self.get_os_info(),
            "python": self.get_python_info(),
        }

        self.logger.info("system_info_collected", info=info)
        return info

    def format_for_display(self, info: Dict[str, Dict]) -> str:
        """Format system info for human-readable display"""
        lines = ["=" * 10, "SYSTEM INFORMATION", "=" * 10]

        if "cpu" in info:
            cpu = info["cpu"]
            lines.append(f"\nCPU:")
            lines.append(f"Processor: {cpu.get('processor', 'Unknown')}")
            lines.append(f"Architecture: {cpu.get('architecture', 'Unknown')}")
            lines.append(f"Cores: {cpu.get('cores_physical', '?')} physical, {cpu.get('cores_logical', '?')} logical")

        if "memory" in info:
            mem = info["memory"]
            lines.append(f"\nMemory:")
            lines.append(f"Total: {mem.get('total_gb', '?')} GB")
            lines.append(f"Available: {mem.get('available_gb', '?')} GB")
            lines.append(f"Used: {mem.get('used_percent', '?')}%")

        if "disk" in info:
            disk = info["disk"]
            lines.append(f"\nDisk:")
            if "filesystem_type" in disk:
                lines.append(f"Filesystem: {disk['filesystem_type']}")
                lines.append(f"Mount Point: {disk['mount_point']}")
                lines.append(f"Device: {disk['device']}")
            lines.append(f"Total: {disk.get('total_gb', '?')} GB")
            lines.append(f"Free: {disk.get('free_gb', '?')} GB")
            lines.append(f"Used: {disk.get('used_percent', '?')}%")

        if "os" in info:
            os_info = info["os"]
            lines.append(f"\nOperating System:")
            lines.append(f"System: {os_info.get('system', 'Unknown')}")
            lines.append(f"Release: {os_info.get('release', 'Unknown')}")
            lines.append(f"Platform: {os_info.get('platform', 'Unknown')}")

        if "python" in info:
            py = info["python"]
            lines.append(f"\nPython:")
            lines.append(f"  Version: {py.get('version', 'Unknown')}")
            lines.append(f"  Implementation: {py.get('implementation', 'Unknown')}")

        lines.append("=" * 60)
        return "\n".join(lines)