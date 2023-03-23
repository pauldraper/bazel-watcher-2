load("@bazel_skylib//lib:shell.bzl", "shell")
load("@rules_file//util:path.bzl", "runfile_path")

def _ibazel_impl(ctx):
    actions = ctx.actions
    bash_runfiles_default = ctx.attr._bash_runfiles[DefaultInfo]
    ibazel = ctx.toolchains[":toolchain_type"]
    name = ctx.attr.name
    template = ctx.file._template
    workspace = ctx.workspace_name

    executable = actions.declare_file(name)
    actions.expand_template(
        is_executable = True,
        substitutions = { 
            "%{exec}": shell.quote(runfile_path(workspace, ibazel.ibazel)),
        },
        template = template,
        output = executable,
    )

    runfiles = ctx.runfiles(files = [ibazel.ibazel])
    runfiles = runfiles.merge(bash_runfiles_default.default_runfiles)
    default_info = DefaultInfo(executable = executable, runfiles = runfiles)

    return [default_info]

ibazel = rule(
    attrs = {
        "_bash_runfiles": attr.label(
            default = "@bazel_tools//tools/bash/runfiles",
        ),
        "_template": attr.label(allow_single_file = True, default = ":runner.sh.tpl"),
    },
    executable = True,
    implementation = _ibazel_impl,
    toolchains = [":toolchain_type"],
)


def _ibazel_toolchain_impl(ctx):
    ibazel = ctx.file.ibazel

    toolchain_info = platform_common.ToolchainInfo(
        ibazel = ibazel
    )

    return [toolchain_info]

ibazel_toolchain = rule(
    implementation = _ibazel_toolchain_impl,
    attrs = {
        "ibazel": attr.label(allow_single_file = True, mandatory = True),
    },
)
