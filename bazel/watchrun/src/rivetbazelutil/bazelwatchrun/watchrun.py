import contextlib
import json
import os
import pathlib
import signal
import subprocess
import queue
import sys
import threading
import time
import typing
from rivetbazelutil.bazelclient import client
from rivetbazelutil.common import run as run_
from rivetbazelutil.ibazelnotifications import notifications
from rules_python.python.runfiles import runfiles

r = runfiles.Create()


def _event_to_notification(event):
    if event["type"] == "BUILD_DONE":
        return notifications.BuildCompleted(notifications.BuildStatus.SUCCESS)
    elif event["type"] == "BUILD_FAILED":
        return notifications.BuildCompleted(notifications.BuildStatus.FAILURE)
    elif event["type"] == "BUILD_START":
        return notifications.BuildStarted()


def _watch(
    workspace, execution_root, executable, name, width, digest_path, events, pass_events
):
    digest = digest_path.read_bytes()
    running = True
    while running:
        run_process = run_.run_executable(
            create_pg=True,
            executable=executable,
            execution_root=execution_root,
            name=name,
            stdin=subprocess.PIPE if pass_events else subprocess.DEVNULL,
            width=width,
            workspace=workspace,
        )

        with run_process as process:
            while True:
                event = events.get()
                if event is None:
                    running = False
                    break
                if event["type"] == "BUILD_DONE":
                    new_digest = digest_path.read_bytes()
                    if digest != new_digest:
                        digest = new_digest
                        break
                if process.stdin:
                    notification = _event_to_notification(event)
                    if notification:
                        try:
                            notifications.write_one(process.stdin, notification)
                        except BrokenPipeError:
                            break
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


@contextlib.contextmanager
def _work(workspace, execution_root, executable, name, width, digest_path, pass_events):
    events = queue.SimpleQueue()
    thread = threading.Thread(
        target=_watch,
        args=(
            workspace,
            execution_root,
            executable,
            name,
            width,
            digest_path,
            events,
            pass_events,
        ),
    )
    thread.start()
    try:
        yield events
    finally:
        events.put(None)
        thread.join()


@contextlib.contextmanager
def _ibazel(ibazel_args, bazel_args, targets):
    pipe_read, pipe_write = os.pipe()

    process = subprocess.Popen(
        [
            r.Rlocation("bazel_watcher/ibazel/ibazel_/ibazel"),
            f"-profile_dev=/dev/fd/{pipe_write}",
        ]
        + [
            "build",
            "--aspects=@rivet_bazel_util//bazel:aspects.bzl%digest",
            "--output_groups=+digest",
        ]
        + ibazel_args
        + bazel_args
        + targets,
        pass_fds=[pipe_write],
    )

    with process:
        try:
            os.close(pipe_write)
            with os.fdopen(pipe_read, "r") as profile:
                yield profile
        finally:
            process.terminate()


def run(
    aliases: typing.Dict[str, str],
    targets: typing.List[str],
    bazel_args: typing.List[str],
    ibazel_args: typing.List[str],
    width: typing.Optional[int],
):
    if width is None:
        width = max(len(aliases.get(target, target)) for target in targets)

    try:
        if not targets:
            while True:
                time.sleep(60)

        info = client.info(["execution_root", "workspace"])
        execution_root = pathlib.Path(info["execution_root"])
        workspace = pathlib.Path(info["workspace"])

        starlark_expr = r"target.files_to_run.executable.path + '\t' + str('digest' in target.output_groups)"
        executables_output = client.cquery(
            " + ".join(targets),
            options=[
                "--output=starlark",
                f"--starlark:expr={starlark_expr}",
            ]
            + bazel_args,
        )
        executables = []
        for line in executables_output.rstrip("\n").split("\n"):
            path_text, pass_events_text = line.split("\t")
            executables.append((pathlib.Path(path_text), pass_events_text == "True"))

        with contextlib.ExitStack() as process_stack:
            ibazel = _ibazel(
                ibazel_args=ibazel_args, bazel_args=bazel_args, targets=targets
            )
            profile = process_stack.enter_context(ibazel)
            workers = []
            for line in profile:
                event = json.loads(line)
                if event["type"] == "BUILD_DONE":
                    if not workers:
                        for target, (executable, pass_events) in zip(
                            targets, executables
                        ):
                            digest_path = pathlib.Path(str(executable) + ".digest")
                            work = _work(
                                workspace,
                                execution_root,
                                executable,
                                aliases.get(target, target),
                                width,
                                digest_path,
                                pass_events,
                            )
                            workers.append(process_stack.enter_context(work))
                for worker in workers:
                    worker.put(event)
    except KeyboardInterrupt:
        sys.exit(130)
