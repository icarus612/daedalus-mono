# libs/python/neural-networks

Four standalone Python packages, all **excluded from the pnpm workspace** (see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo)) — none of them wired into `turbo build/dev/lint/test`.

| Package | Docs |
|---|---|
| `abstract-base-classes` | [abstract-base-classes/README.md](abstract-base-classes/README.md) |
| `digit-recognition` | [digit-recognition/README.md](digit-recognition/README.md) |
| `market-analyzer` | [market-analyzer/README.md](market-analyzer/README.md) |
| `open-ai-gym` | [open-ai-gym/README.md](open-ai-gym/README.md) |

`market-analyzer` also contains a stray, empty (0 byte) Bazel `BUILD` file — vestigial, see [../../../architecture.md](../../../architecture.md#bazel-legacy-unused).
