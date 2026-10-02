"""Smoke-test both distribution formats in separate clean environments."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


def check_artifact(artifact: Path, expected_version: str) -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory(prefix="skill-factory-package-") as tmp:
        root = Path(tmp)
        venv = root / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, env=env)
        bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        cli = bin_dir / ("skill-factory.exe" if os.name == "nt" else "skill-factory")
        work = root / "work"
        work.mkdir()

        def run(*args: str) -> None:
            process = subprocess.Popen(args, cwd=work, env=env, start_new_session=os.name != "nt")
            try:
                returncode = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                # Build isolation can spawn pip children that keep the venv locked on Windows.
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, check=False)
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            if returncode:
                raise subprocess.CalledProcessError(returncode, args)

        run(str(python), "-m", "pip", "--disable-pip-version-check", "install", str(artifact))
        run(str(python), "-m", "pip", "check")
        code = (
            "import importlib.metadata as m; import skill_factory; "
            f"assert m.version('agent-skill-factory') == skill_factory.__version__ == {expected_version!r}"
        )
        run(str(python), "-I", "-c", code)
        run(str(cli), "--version")
        run(str(cli), "init", ".")
        plan = {
            "schema_version": 1, "name": "package-smoke",
            "description": "Use when validating CSV experiment inputs against an explicit column contract before analysis.",
            "brief": "Check the declared input contract.",
            "workflow": ["Read references/contract.md and inspect the input columns."],
            "quality_checks": ["Report source row numbers for every finding."],
            "constraints": ["Keep the original input unchanged."],
            "examples": ["Check this CSV experiment input."],
            "resource_files": [{"path": "references/contract.md", "content": "ID must be unique.\n",
                                "purpose": "Read before checking ID values."}],
        }
        (work / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        run(str(cli), "generate", "--from-plan", "plan.json", "--output", "skills")
        run(str(cli), "lint", "skills/package-smoke", "--policy", "strict")
        run(str(cli), "eval-generate", "--from-plan", "plan.json", "--output", "skills/package-smoke/evals/evals.json")
        run(str(cli), "eval", "skills/package-smoke")
        run(str(cli), "registry", "add", "skills/package-smoke", "--version", "1.0.0")
        run(str(cli), "install", "package-smoke", "--output", "installed")
        assert (work / "installed/package-smoke/references/contract.md").read_text(encoding="utf-8") == "ID must be unique.\n"
        print(f"PASS clean install: {artifact.name}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    for pattern in (f"agent_skill_factory-{args.expected_version}-*.whl", f"agent_skill_factory-{args.expected_version}.tar.gz"):
        artifacts = list(args.dist_dir.glob(pattern))
        if len(artifacts) != 1:
            parser.error(f"Expected exactly one artifact matching {pattern} in {args.dist_dir}")
        check_artifact(artifacts[0].resolve(), args.expected_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
