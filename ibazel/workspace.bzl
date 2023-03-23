load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")
load(":ibazel.bzl", "IBAZEL_REPOS")

def ibazel_repositories(version = "v0.21.4"):
    for name, info in IBAZEL_REPOS[version].items():
        http_file(
            name = "ibazel_%s" % name,
            executable = True,
            sha256 = info.sha256,
            url = "https://github.com/bazelbuild/bazel-watcher/releases/download/%s/%s" % (version, info.path),
        )

def ibazel_toolchains():
    native.register_toolchains(
        "@rivet_bazel_util//ibazel:macos_amd64_toolchain",
        "@rivet_bazel_util//ibazel:macos_arm64_toolchain",
        "@rivet_bazel_util//ibazel:linux_amd64_toolchain",
        "@rivet_bazel_util//ibazel:linux_arm64_toolchain",
        "@rivet_bazel_util//ibazel:windows_amd64_toolchain",
        "@rivet_bazel_util//ibazel:src_toolchain",
    )
