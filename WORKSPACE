workspace(name = "daedalus_mono")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Node.js rules
http_archive(
    name = "build_bazel_rules_nodejs",
    sha256 = "2a8d2b37f0850789e4a2cf16e2c2f6f2a6c8fdef6e2dd490a3f0181a0c1b2a49",
    urls = ["https://github.com/bazelbuild/rules_nodejs/releases/download/4.4.6/rules_nodejs-4.4.6.tar.gz"],
)

load("@build_bazel_rules_nodejs//:index.bzl", "node_repositories", "pnpm_install")

node_repositories(package_json = ["//:package.json"])

pnpm_install(
    name = "npm",
    package_json = "//:package.json",
    lock_file = "//:pnpm-lock.yaml",
)

# Python rules
http_archive(
    name = "rules_python",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.4.0/rules_python-0.4.0.tar.gz",
    sha256 = "954aa89b491be4a083304a2cb838019c8b8c3720a7abb9c4cb81ac7a24230cea",
)

load("@rules_python//python:pip.bzl", "pip_repositories")

pip_repositories()

# Go rules
http_archive(
    name = "io_bazel_rules_go",
    urls = ["https://github.com/bazelbuild/rules_go/releases/download/v0.29.0/rules_go-v0.29.0.tar.gz"],
    sha256 = "a82a352bffae6bee4e95f68a8d80a70e87f42c4741e6a448bec11998fcc82329",
)

load("@io_bazel_rules_go//go:deps.bzl", "go_rules_dependencies", "go_register_toolchains")

go_rules_dependencies()

go_register_toolchains()