"""Run N bot games in parallel, aggregate success rate and causes of death."""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(BASE, "venv", "bin", "python")
MAIN = os.path.join(BASE, "bot", "main.py")


def run_game(args):
    outdir, gid, timeout = args
    proc = subprocess.Popen([PY, MAIN, outdir, "--id", gid],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()  # SIGTERM -> bot writes meta.json (result=terminated)
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    meta_path = os.path.join(outdir, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    return {"id": gid, "result": "no_meta"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batchdir")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=2700)
    args = ap.parse_args()

    os.makedirs(args.batchdir, exist_ok=True)
    jobs = []
    for i in range(args.n):
        gid = f"g{i:04d}"
        jobs.append((os.path.join(args.batchdir, gid), gid, args.timeout))

    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_game, j): j[1] for j in jobs}
        for fut in as_completed(futs):
            meta = fut.result()
            results.append(meta)
            n_ok = sum(1 for r in results if r.get("result") in ("minetown", "quest"))
            print(f"[{len(results)}/{args.n}] {meta.get('id')}: {meta.get('result')} "
                  f"branch={meta.get('branch')} dlvl={meta.get('dlvl')} T={meta.get('turn')} "
                  f"death={meta.get('death')!r}  | success so far: {n_ok}/{len(results)}",
                  flush=True)

    n_ok = sum(1 for r in results if r.get("result") in ("minetown", "quest"))
    print("\n========== SUMMARY ==========")
    print(f"games: {len(results)}  minetown: {n_ok}  rate: {100.0*n_ok/max(1,len(results)):.1f}%")
    print(f"wall time: {(time.time()-t0)/60:.1f} min")
    print("\nresults breakdown:")
    for k, v in Counter(r.get("result") for r in results).most_common():
        print(f"  {v:3d}  {k}")
    print("\ndeaths breakdown:")
    for k, v in Counter(r.get("death") for r in results if r.get("death")).most_common(15):
        print(f"  {v:3d}  {k}")
    print("\nfailures by branch/dlvl:")
    fails = Counter((r.get("branch"), r.get("dlvl")) for r in results
                    if r.get("result") != "minetown")
    for k, v in fails.most_common(15):
        print(f"  {v:3d}  {k}")

    with open(os.path.join(args.batchdir, "summary.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
