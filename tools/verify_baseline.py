#!/usr/bin/env python3
"""Read-only baseline check. A mismatch means inspect/rebase, never reset local changes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    args=p.parse_args()
    package=Path(__file__).resolve().parents[1]
    baseline=json.loads((package/"baseline.json").read_text())
    results=[]
    for relative,expected in baseline["verified_git_blobs"].items():
        path=args.repo/relative
        content=path.read_bytes() if path.is_file() else None
        actual=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest() if content is not None else None
        results.append({"path":relative,"expected":expected,"actual":actual,"matches":actual==expected})
    head=subprocess.run(["git","-C",str(args.repo),"rev-parse","HEAD"],capture_output=True,text=True)
    report={"expected_commit":baseline["commit"],"actual_commit":head.stdout.strip() if head.returncode==0 else None,"files":results}
    print(json.dumps(report,indent=2))
    return 0 if all(row["matches"] for row in results) else 2

if __name__=="__main__":
    raise SystemExit(main())
