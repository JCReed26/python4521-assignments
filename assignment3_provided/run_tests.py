#!/usr/bin/env python3
import argparse
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List


def run_cmd(cmd: List[str]) -> Tuple[int, str, str, float]:
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    dt = time.perf_counter() - t0
    return proc.returncode, proc.stdout, proc.stderr, dt


def read_outputs(size: int, steps: int, suffix: str) -> Dict[int, str]:
    outputs = {}
    for init_idx in (1, 2, 3, 4):
        fname = f"output_grid{init_idx}_{size}_{steps}_{suffix}.txt"
        with open(fname, "r", encoding="utf-8") as f:
            outputs[init_idx] = f.read()
    return outputs


def compare_outputs(seq_out: Dict[int, str], par_out: Dict[int, str]) -> Tuple[Dict[int, bool], bool]:
    results = {}
    for k in (1, 2, 3, 4):
        results[k] = (seq_out.get(k, None) == par_out.get(k, None))
    overall = all(results.values())
    return results, overall


def cap_nprocs(requested: int, grid_size: int, cpu_count: int) -> int:
    # Per rubric: nprocs ≤ grid_size or ≤ 16; also never exceed cpu_count
    return max(1, min(requested, grid_size, 16, cpu_count))


def run_seq(seq_path: str, size: int, steps: int) -> Tuple[float, Dict[int, str]]:
    cmd = [sys.executable, seq_path, str(size), str(steps)]
    rc, out, err, dt = run_cmd(cmd)
    if rc != 0:
        raise RuntimeError(f"Sequential run failed (rc={rc}) for size={size}, steps={steps}:\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    outputs = read_outputs(size, steps, "seq")
    return dt, outputs


def run_par(par_path: str, size: int, steps: int, nprocs: int) -> Tuple[float, Dict[int, str]]:
    cmd = [sys.executable, par_path, str(size), str(steps), str(nprocs)]
    rc, out, err, dt = run_cmd(cmd)
    if rc != 0:
        raise RuntimeError(f"Parallel run failed (rc={rc}) for size={size}, steps={steps}, nprocs={nprocs}:\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    outputs = read_outputs(size, steps, "MP")
    return dt, outputs


def print_header(title: str):
    print(f"\n== {title} ==")


def main():
    parser = argparse.ArgumentParser(description="Run correctness and performance tests for Assignment 3.")
    parser.add_argument("parallel", help="Path to the parallel implementation (e.g., reed_j_assignment3.py)")
    parser.add_argument("sequential", help="Path to the sequential implementation (e.g., seq_assignment3.py)")
    parser.add_argument("--steps", type=int, default=20, help="Number of steps/iterations (default: 20)")
    parser.add_argument("--full", action="store_true", help="Run full suite (includes 1024x1024 correctness and speedups)")
    parser.add_argument("--quick", action="store_true", help="Run only quick correctness (10x10 with 2 and 4 procs)")
    args = parser.parse_args()

    # Default behavior: quick unless --full is provided
    quick = args.quick or (not args.full)

    base_dir = Path.cwd()
    par_path = (base_dir / args.parallel).as_posix()
    seq_path = (base_dir / args.sequential).as_posix()

    if not Path(par_path).exists():
        print(f"error: parallel file not found: {par_path}", file=sys.stderr)
        sys.exit(2)
    if not Path(seq_path).exists():
        print(f"error: sequential file not found: {seq_path}", file=sys.stderr)
        sys.exit(2)

    steps = int(args.steps)

    # Quick suite: 10x10 correctness for nprocs 2 and 4
    if quick:
        size = 10
        print_header(f"Correctness: {size}x{size}, steps={steps}, nprocs=2 and 4")
        # Run sequential once
        try:
            t_seq_10, seq_out_10 = run_seq(seq_path, size, steps)
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

        for req_n in (2, 4):
            n = cap_nprocs(req_n, size, os.cpu_count() or 1)
            try:
                t_par, par_out = run_par(par_path, size, steps, n)
            except Exception as e:
                print(str(e), file=sys.stderr)
                sys.exit(1)
            per_init, overall = compare_outputs(seq_out_10, par_out)
            print(f"nprocs={n}: overall={'PASS' if overall else 'FAIL'}; details="
                  f"init1={'ok' if per_init[1] else 'x'}, init2={'ok' if per_init[2] else 'x'}, "
                  f"init3={'ok' if per_init[3] else 'x'}, init4={'ok' if per_init[4] else 'x'}")

    # Full suite: 1024x1024 correctness and speedups
    if args.full:
        size = 1024
        print_header(f"Correctness: {size}x{size}, steps={steps}, nprocs=2 and 4")

        # Baseline sequential
        try:
            t_seq_1024, seq_out_1024 = run_seq(seq_path, size, steps)
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
        print(f"sequential time: {t_seq_1024:.3f}s")

        # Correctness and performance for nprocs 2 and 4
        speedups: Dict[int, float] = {}
        for req_n in (2, 4):
            n = cap_nprocs(req_n, size, os.cpu_count() or 1)
            try:
                t_par, par_out = run_par(par_path, size, steps, n)
            except Exception as e:
                print(str(e), file=sys.stderr)
                sys.exit(1)
            per_init, overall = compare_outputs(seq_out_1024, par_out)
            sp = (t_seq_1024 / t_par) if t_par > 0 else float('inf')
            speedups[n] = sp
            print(f"nprocs={n}: overall={'PASS' if overall else 'FAIL'}; speedup={sp:.2f}x; details="
                  f"init1={'ok' if per_init[1] else 'x'}, init2={'ok' if per_init[2] else 'x'}, "
                  f"init3={'ok' if per_init[3] else 'x'}, init4={'ok' if per_init[4] else 'x'}")

        # Additional speedups for nprocs in {1,2,4,8,16}
        print_header(f"Speedups: {size}x{size}, steps={steps}, nprocs in [1,2,4,8,16]")
        requested = [1, 2, 4, 8, 16]
        effective = []
        for r in requested:
            n = cap_nprocs(r, size, os.cpu_count() or 1)
            if n not in effective:
                effective.append(n)

        # We already measured 2 and 4 above if effective included them
        for n in effective:
            if n in speedups:
                continue
            try:
                t_par, _ = run_par(par_path, size, steps, n)
            except Exception as e:
                print(str(e), file=sys.stderr)
                sys.exit(1)
            sp = (t_seq_1024 / t_par) if t_par > 0 else float('inf')
            speedups[n] = sp

        # Summarize speedup checks
        # 20% speedup for nprocs=2 and 4
        for req in (2, 4):
            n = cap_nprocs(req, size, os.cpu_count() or 1)
            sp = speedups.get(n)
            if sp is None:
                print(f"nprocs={n}: no measurement available")
            else:
                print(f"nprocs={n}: speedup={sp:.2f}x -> {'PASS' if sp >= 1.20 else 'FAIL'} (>=1.20x)")

        # Any nprocs achieving 4x
        any_4x = any(sp >= 4.0 for sp in speedups.values())
        print(f"any nprocs >=4.00x: {'PASS' if any_4x else 'FAIL'}")

    print("\nDone.")


if __name__ == "__main__":
    main()

