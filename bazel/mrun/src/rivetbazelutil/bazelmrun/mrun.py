import contextlib
import json
import os
import pathlib
import subprocess
import sys
from concurrent import futures
from rivetbazelutil.bazelclient import client
from rivetbazelutil.common import run as run_


def _run_one(workspace, execution_root, executable, name, width):
    p = run_.run_executable(
        display_code=True,
        executable=executable,
        execution_root=execution_root,
        name=name,
        stdin=subprocess.DEVNULL,
        width=width,
        workspace=workspace,
    )
    with p as process:
        process.wait()
        return process.returncode


def run(aliases, targets, width, bazel_args, parallelism):
    if width is None:
        width = max(len(aliases.get(target, target)) for target in targets)

    info = client.info(["execution_root", "workspace"])
    execution_root = pathlib.Path(info["execution_root"])
    workspace = pathlib.Path(info["workspace"])

    starlark_expr = "target.files_to_run.executable.path"
    executables_output = client.cquery(
        " + ".join(targets),
        options=["--output=starlark", f"--starlark:expr={starlark_expr}"] + bazel_args,
    )
    executables = [
        pathlib.Path(path) for path in executables_output.rstrip("\n").split("\n")
    ]

    client.build(targets, options=bazel_args)

    code = 0
    with futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures_ = [
            executor.submit(
                _run_one,
                workspace,
                execution_root,
                executable,
                aliases.get(target, target),
                width,
            )
            for target, executable in zip(targets, executables)
        ]
        for future in futures.as_completed(futures_):
            result = future.result()
            if result is None:
                code = 127
            elif result and not code:
                code = result
    sys.exit(code)
