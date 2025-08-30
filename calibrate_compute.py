#!/usr/bin/env python3
"""
Compute calibration utility for long-running pipeline (python main.py run_all).

This script:
- Launches the target command (default: "python main.py run_all") in a new process group
- Samples system and process resource usage at a fixed interval for a fixed duration
- Computes peak and 95th percentile metrics for CPU, RAM, disk I/O, and network I/O
- Measures on-disk growth across key project directories
- Emits a JSON and Markdown report with recommended minimum specs

Usage:
  python calibrate_compute.py \
    --cmd "python main.py run_all" \
    --duration-seconds 600 \
    --sample-interval 1.0

Notes:
- Requires psutil. If not installed: pip install psutil
- The target command is terminated gracefully after sampling (SIGINT, then SIGTERM)
"""

import argparse
import datetime as _dt
import json
import math
import os
import shutil
import signal
import statistics
import subprocess
import sys
import time
from typing import Dict, List, Tuple


def _require_psutil():
    try:
        import psutil  # type: ignore
        return psutil
    except Exception as exc:  # pragma: no cover
        print(
            "\nERROR: psutil is required. Install it with: pip install psutil\n",
            file=sys.stderr,
        )
        raise


def _bytes_to_human(n: float) -> str:
    if n is None:
        return "N/A"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    return f"{n:.2f} {units[i]}"


def _safe_percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data_sorted[int(k)]
    d0 = data_sorted[f] * (c - k)
    d1 = data_sorted[c] * (k - f)
    return d0 + d1


def _list_project_dirs() -> List[str]:
    # Key dirs whose growth matters for sustained operation
    candidates = [
        "logs",
        "data",
        "cache",
        "models",
        "content_plan_backups",
        "exported_content_plans",
        "chroma_db",
        os.path.join("Module2", "logs"),
        os.path.join("Module2", "cache"),
        os.path.join("Module2", "models"),
    ]
    existing = []
    for d in candidates:
        if os.path.isdir(d):
            existing.append(d)
    return existing


def _dir_size_bytes(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                fp = os.path.join(root, name)
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def _measure_dirs_sizes(dirs: List[str]) -> Dict[str, int]:
    return {d: _dir_size_bytes(d) for d in dirs}


def _terminate_process_group(proc: subprocess.Popen, timeout: float = 20.0) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            return
        time.sleep(0.2)
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass


def _gather_process_tree_memory_bytes(psutil, root_proc) -> int:
    total = 0
    try:
        procs = [root_proc] + root_proc.children(recursive=True)
    except Exception:
        procs = [root_proc]
    for p in procs:
        try:
            mem = p.memory_info().rss
            total += int(mem)
        except Exception:
            continue
    return total


def calibrate(cmd: str, duration_seconds: float, sample_interval: float) -> Dict:
    psutil = _require_psutil()

    # Prepare output folder
    out_dir = os.path.join("logs", "compute_calibration")
    os.makedirs(out_dir, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Directories growth baseline
    track_dirs = _list_project_dirs()
    before_sizes = _measure_dirs_sizes(track_dirs)

    # Launch target command in new session (own process group)
    proc = subprocess.Popen(
        cmd,
        shell=True,
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Attach psutil to process
    try:
        p = psutil.Process(proc.pid)
    except Exception as e:
        _terminate_process_group(proc)
        raise RuntimeError(f"Failed to attach to process: {e}")

    # Warm up CPU measurement
    try:
        p.cpu_percent(interval=None)
    except Exception:
        pass

    # Storage for samples
    samples = {
        "time": [],
        "cpu_total_percent": [],
        "cpu_process_percent": [],
        "ram_used_bytes": [],
        "ram_process_tree_bytes": [],
        "disk_read_bytes": [],
        "disk_write_bytes": [],
        "net_bytes_sent": [],
        "net_bytes_recv": [],
    }

    # Baselines for I/O deltas
    prev_disk = psutil.disk_io_counters() if hasattr(psutil, "disk_io_counters") else None
    prev_net = psutil.net_io_counters() if hasattr(psutil, "net_io_counters") else None

    start_time = time.time()
    next_tick = start_time
    try:
        while time.time() - start_time < duration_seconds:
            now = time.time()
            samples["time"].append(now - start_time)

            # System-wide CPU percent (since last call)
            try:
                cpu_total = psutil.cpu_percent(interval=None)
            except Exception:
                cpu_total = 0.0

            # Process CPU percent
            try:
                cpu_proc = p.cpu_percent(interval=None)
            except Exception:
                cpu_proc = 0.0

            # RAM: system used and process tree RSS
            try:
                vm = psutil.virtual_memory()
                ram_used = int(vm.used)
            except Exception:
                ram_used = 0

            ram_tree = _gather_process_tree_memory_bytes(psutil, p)

            # Disk I/O deltas
            read_bytes = write_bytes = 0
            try:
                cur_disk = psutil.disk_io_counters()
                if prev_disk is not None and cur_disk is not None:
                    read_bytes = max(0, int(cur_disk.read_bytes) - int(prev_disk.read_bytes))
                    write_bytes = max(0, int(cur_disk.write_bytes) - int(prev_disk.write_bytes))
                prev_disk = cur_disk
            except Exception:
                pass

            # Net I/O deltas
            bytes_sent = bytes_recv = 0
            try:
                cur_net = psutil.net_io_counters()
                if prev_net is not None and cur_net is not None:
                    bytes_sent = max(0, int(cur_net.bytes_sent) - int(prev_net.bytes_sent))
                    bytes_recv = max(0, int(cur_net.bytes_recv) - int(prev_net.bytes_recv))
                prev_net = cur_net
            except Exception:
                pass

            samples["cpu_total_percent"].append(float(cpu_total))
            samples["cpu_process_percent"].append(float(cpu_proc))
            samples["ram_used_bytes"].append(int(ram_used))
            samples["ram_process_tree_bytes"].append(int(ram_tree))
            samples["disk_read_bytes"].append(int(read_bytes))
            samples["disk_write_bytes"].append(int(write_bytes))
            samples["net_bytes_sent"].append(int(bytes_sent))
            samples["net_bytes_recv"].append(int(bytes_recv))

            next_tick += sample_interval
            sleep_for = max(0.0, next_tick - time.time())
            time.sleep(sleep_for)
    finally:
        _terminate_process_group(proc)
        # Drain output pipes best-effort to avoid zombies
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except Exception:
            stdout = stderr = None

    # After sizes for directories
    after_sizes = _measure_dirs_sizes(track_dirs)

    # Compute aggregates
    def agg(arr: List[float]) -> Dict[str, float]:
        return {
            "avg": float(statistics.fmean(arr)) if arr else 0.0,
            "p95": float(_safe_percentile(arr, 0.95)) if arr else 0.0,
            "max": float(max(arr)) if arr else 0.0,
        }

    cpu_total = agg(samples["cpu_total_percent"])
    cpu_proc = agg(samples["cpu_process_percent"])
    ram_sys = agg([float(x) for x in samples["ram_used_bytes"]])
    ram_proc_tree = agg([float(x) for x in samples["ram_process_tree_bytes"]])
    disk_r = agg([float(x) / sample_interval for x in samples["disk_read_bytes"]])
    disk_w = agg([float(x) / sample_interval for x in samples["disk_write_bytes"]])
    net_s = agg([float(x) / sample_interval for x in samples["net_bytes_sent"]])
    net_r = agg([float(x) / sample_interval for x in samples["net_bytes_recv"]])

    # Directory growth per minute
    growth: Dict[str, Dict[str, float]] = {}
    duration_minutes = max(1e-6, duration_seconds / 60.0)
    for d in track_dirs:
        before = before_sizes.get(d, 0)
        after = after_sizes.get(d, 0)
        delta = max(0, after - before)
        per_min = float(delta) / duration_minutes
        growth[d] = {
            "before_bytes": float(before),
            "after_bytes": float(after),
            "delta_bytes": float(delta),
            "delta_per_minute_bytes": float(per_min),
        }

    # Recommend specs with headroom multipliers
    # RAM: 2.0x max observed process tree memory, but minimum 2 GB
    recommended_ram_bytes = max(2 * int(ram_proc_tree["max"]), 2 * 1024 * 1024 * 1024)
    # CPU: recommend cores = ceil(p95 total cpu percent / 75) to keep below 75% per core
    # plus at least 2 cores
    recommended_cores = max(2, int(math.ceil(cpu_total["p95"] / 75.0)))
    # Disk throughput: 2x p95 write and read
    recommended_disk_write_bps = 2 * int(disk_w["p95"])  # bytes/sec
    recommended_disk_read_bps = 2 * int(disk_r["p95"])   # bytes/sec
    # Network throughput: 2x p95 send/recv
    recommended_net_up_bps = 2 * int(net_s["p95"])       # bytes/sec
    recommended_net_down_bps = 2 * int(net_r["p95"])     # bytes/sec
    # Disk capacity: existing size of tracked dirs + 7 days of growth at 2x safety
    existing_bytes = sum(after_sizes.values())
    per_min_total = sum(v["delta_per_minute_bytes"] for v in growth.values())
    recommended_disk_capacity_bytes = int(existing_bytes + (per_min_total * 60 * 24 * 7 * 2))

    report = {
        "timestamp": ts,
        "command": cmd,
        "duration_seconds": duration_seconds,
        "sample_interval_seconds": sample_interval,
        "system": {
            "cpu_total_percent": cpu_total,
            "ram_used_bytes": ram_sys,
            "disk_read_bytes_per_sec": disk_r,
            "disk_write_bytes_per_sec": disk_w,
            "net_sent_bytes_per_sec": net_s,
            "net_recv_bytes_per_sec": net_r,
        },
        "process_tree": {
            "cpu_process_percent": cpu_proc,
            "ram_process_tree_bytes": ram_proc_tree,
        },
        "directories": {
            "tracked": track_dirs,
            "sizes_before": before_sizes,
            "sizes_after": after_sizes,
            "growth": growth,
        },
        "recommendations": {
            "ram_min_bytes": recommended_ram_bytes,
            "cpu_cores_min": recommended_cores,
            "disk_write_min_bps": recommended_disk_write_bps,
            "disk_read_min_bps": recommended_disk_read_bps,
            "net_up_min_bps": recommended_net_up_bps,
            "net_down_min_bps": recommended_net_down_bps,
            "disk_capacity_min_bytes": recommended_disk_capacity_bytes,
        },
    }

    json_path = os.path.join(out_dir, f"report_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_path = os.path.join(out_dir, f"report_{ts}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Compute Calibration Report ({ts})\n\n")
        f.write(f"Command: `{cmd}`\n\n")
        f.write(f"Duration: {duration_seconds:.1f}s, Sample interval: {sample_interval:.2f}s\n\n")
        f.write("## Observed Metrics (95th percentile / max)\n\n")
        f.write(
            f"- CPU total: p95 {report['system']['cpu_total_percent']['p95']:.1f}% / max {report['system']['cpu_total_percent']['max']:.1f}%\n"
        )
        f.write(
            f"- CPU process: p95 {report['process_tree']['cpu_process_percent']['p95']:.1f}% / max {report['process_tree']['cpu_process_percent']['max']:.1f}%\n"
        )
        f.write(
            f"- RAM process tree: p95 {_bytes_to_human(report['process_tree']['ram_process_tree_bytes']['p95'])} / max {_bytes_to_human(report['process_tree']['ram_process_tree_bytes']['max'])}\n"
        )
        f.write(
            f"- Disk write: p95 {_bytes_to_human(report['system']['disk_write_bytes_per_sec']['p95'])}/s\n"
        )
        f.write(
            f"- Disk read: p95 {_bytes_to_human(report['system']['disk_read_bytes_per_sec']['p95'])}/s\n"
        )
        f.write(
            f"- Net up: p95 {_bytes_to_human(report['system']['net_sent_bytes_per_sec']['p95'])}/s\n"
        )
        f.write(
            f"- Net down: p95 {_bytes_to_human(report['system']['net_recv_bytes_per_sec']['p95'])}/s\n\n"
        )
        f.write("## Directory Growth (bytes/min)\n\n")
        for d, g in growth.items():
            f.write(
                f"- {d}: +{_bytes_to_human(g['delta_bytes'])} total, +{_bytes_to_human(g['delta_per_minute_bytes'])}/min\n"
            )
        f.write("\n## Recommended Minimum Specs\n\n")
        f.write(
            f"- RAM: {_bytes_to_human(recommended_ram_bytes)}\n"
        )
        f.write(
            f"- CPU cores: {recommended_cores}\n"
        )
        f.write(
            f"- Disk throughput: write >= {_bytes_to_human(recommended_disk_write_bps)}/s, read >= {_bytes_to_human(recommended_disk_read_bps)}/s\n"
        )
        f.write(
            f"- Network: up >= {_bytes_to_human(recommended_net_up_bps)}/s, down >= {_bytes_to_human(recommended_net_down_bps)}/s\n"
        )
        f.write(
            f"- Disk capacity (7d): >= {_bytes_to_human(recommended_disk_capacity_bytes)}\n"
        )
        f.write("\n")

    return {
        "json_path": json_path,
        "md_path": md_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute calibration for run_all")
    parser.add_argument(
        "--cmd",
        default="python main.py run_all",
        help="Command to execute for calibration (non-terminating pipeline)",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=600.0,
        help="Total sampling duration in seconds",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=1.0,
        help="Sampling interval in seconds",
    )
    args = parser.parse_args()

    result_paths = calibrate(
        cmd=args.cmd,
        duration_seconds=args.duration_seconds,
        sample_interval=args.sample_interval,
    )
    print(
        f"Calibration complete. Reports saved to:\n  {result_paths['json_path']}\n  {result_paths['md_path']}"
    )


if __name__ == "__main__":
    main()


