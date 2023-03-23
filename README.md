# Bazel Util

Bazel utilities

## Overview

- **bazel-mrun:** Build and run multiple targets in parallel.
- **bazel-watchrun:** Build and run multiple targets, restarting them after
  changes.

## Install

### Bazel repositority

Add this project as a Bazel repository to the workspace:

<details>
<summary>WORKSPACE.bazel</summary>

```bzl
# Rivet Bazel Util

RIVET_BAZEL_UTIL_VERSION = "..." # commit

http_archive(
    name = "rivet_bazel_util",
    # sha256 = "...", # digest
    strip_prefix = "rivet-bazel-util-%s" % RIVET_BAZEL_UTIL_VERSION,
    url = "https://github.com/rivethealth/rivet-bazel-util/archive/%s.tar.gz" % RIVET_BAZEL_UTIL_VERSION,
)

load("@rivet_bazel_util//ibazel:workspace.bzl", "ibazel_repositories", "ibazel_toolchains")

ibazel_repositories()

ibazel_toolchains()
```

The `@rivet_bazel_util//ibazel:toolchain_type` toolchain will download a
pre-build executable of ibazel, if it exists. Otherwise, it will rely on
`@bazel-watcher` repo to build from source.

</details>

The targets can be invoked:

```sh
bazel run @rivet_bazel_util//mrun:bin -- target1 target2
bazel run @rivet_bazel_util//watchrun:bin -- target1 target2
```

### Linux

Or it can be installed natively, by building and installing a tarball.

<details>
<summary>Installation</summary>

```sh
bazel build bazel:tar

rm -fr /opt/rivet-bazel-util mkdir /opt/rivet-bazel-util tar xf
bazel-bin/bazel/tar.tar -C /opt/rivet-bazel-util

printf '#!/bin/sh -e\nexec /opt/rivet-bazel-util/mrun "$@"\n' > /usr/local/bin/bazel-mrun
chmod +x /usr/local/bin/bazel-mrun
printf '#!/bin/sh -e\nexec /opt/rivet-bazel-util/watchrun "$@"\n' > /usr/local/bin/bazel-watchrun
chmod +x /usr/local/bin/bazel-watchrun
```

</details>

Note that bazel-watchrun relies on an aspect, and therefore still requires
adding the rivet_bazel_util repository to the workspace.

## Features

### bazel-mrun

Build and run multiple targets in parallel. Like
[`bazel run`](https://bazel.build/docs/user-manual#running-executables), but for
multiple targets.

#### Usage

<details>
<summary>Usage</summary>

```txt
usage: bazel-mrun [-h] [--alias TARGET=ALIAS] [--bazel-arg BAZEL_ARG]
                  [--parallelism PARALLELISM] [--width WIDTH]
                  [target [target ...]]

Build and run Bazel executables.

positional arguments:
  target                Targets to run

optional arguments:
  -h, --help            show this help message and exit
  --alias TARGET=ALIAS  aliases
  --bazel-arg BAZEL_ARG
                        bazel argument
  --parallelism PARALLELISM
                        maximum concurrent processes
  --width WIDTH
```

</details>

#### Implementation

<details>
<summary>Implementation</summary>

1. Query Bazel for the excutable outputs.
2. Builds the targets in parallel using `bazel build`.
3. Run each executable in parallel.
4. Prefix stdout and stderr with the target's name.
</details>

### bazel-watchrun

Build and run multiple targets, restarting them after changes. Like
[`ibazel run`](https://github.com/bazelbuild/bazel-watcher), but for multiple
targets.

#### Usage

<details>
<summary>Usage</summary>

```txt
usage: bazel-watchrun [-h] [--alias TARGET=NAME] [--bazel-arg BAZEL_ARG]
                      [--ibazel-arg IBAZEL_ARG] [--width WIDTH]
                      [target [target ...]]

Build and run Bazel executables.

positional arguments: target Targets to run

optional arguments: -h, --help show this help message and exit --alias
TARGET=NAME --bazel-arg BAZEL_ARG bazel argument --ibazel-arg IBAZEL_ARG ibazel
argument --width WIDTH
```

</details>

#### Controlling restarts

A target can control when it restarts by providing a `digest`
[output group](https://bazel.build/extending/rules#requesting_output_files)
consisting of a single file. The executable is restarted when the contents of
that file change. Bazel-watchrun will also send the executable
[ibazel-like events](https://github.com/bazelbuild/bazel-watcher#running-a-target)
on stdin.

For example, consider a webpack server. Changes to Node.js files (weback config,
npm dependencies) should trigger a restart, but changes to browser sources
should be quickly rebundled without a full process restart. To accomplish this,
the target provides a `digest` output group for the Node.js sources, and the
executable listens for build success notifications on stdin and checks for
changed browser sources.

#### Implementation

<details>
<summary>Implementation</summary>

1. Query Bazel for the excutable outputs.
2. Watch and rebuild the targets in parallel using `ibazel build`, including the
   additional `digest` output group. If the target does not already provide the
   `digest` output group, an aspect generates it by hashing the executable and
   runfile tree.
3. Read the profile events from ibazel. Each time a build is completed, check
   the digests, and restart any executable with a changed digest.
4. If the target provided its own digest, pass write ibazel-like events to its
   stdin.
5. Prefix stdout and stderr with the target's name.
</details>
