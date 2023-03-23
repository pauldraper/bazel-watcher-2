IBAZEL_REPO_NAMES = [
    "darwin_amd64",
    "darwin_arm64",
    "linux_amd64",
    "linux_arm64",
    "windows_amd64",
]

IBAZEL_REPOS = {
    "v0.21.4": {
        "darwin_amd64": struct(
            path = "ibazel_darwin_amd64",
            sha256 = "55254ce8813a7a39505c5804d352a7d0c183994c6ed56b1ed5b18b3753dbbebb",
        ),
        "darwin_arm64": struct(
            path = "ibazel_darwin_arm64",
            sha256 = "c539b5094e4b48bc10e003ebf5fda7283467e3b96754b0b7a617a2d516a4493f",
        ),
        "linux_amd64": struct(
            path = "ibazel_linux_amd64",
            sha256 = "149befe61e53c69ededa0aabcd4a305b60e176ba042a712c5e8e19f37f551684"
        ),
        "linux_arm64": struct(
            path = "ibazel_linux_arm64",
            sha256 = "51cf754b876942c93569e32e99171061cf3db15a5877b22989d4ea36c1b319b7",
        ),
        "windows_amd64": struct(
            path = "ibazel_windows_amd64.exe",
            sha256 = "92b45ff697a98706f7d26547185d282350dd994e76185705406845e88d624565",
        )
    }
}
