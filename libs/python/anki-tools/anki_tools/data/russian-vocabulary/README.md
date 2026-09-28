# Russian Vocabulary Source Data

Exported from `russian_vocabulary.xlsx` on 2026-09-26.

## Regenerating

Run from `libs/python/anki-tools`:

```
uv run python -m anki_tools.vocabulary_source --out-dir anki_tools/data/russian-vocabulary
```

## Sheet → file mapping

| Sheet      | File            |
| ---------- | ---------------- |
| Nouns      | nouns.tsv        |
| Verbs      | verbs.tsv        |
| Adjectives | adjectives.tsv   |
| Adverbs    | adverbs.tsv      |

## Build input

These four TSV files are the build input for everything downstream in this package — not the original workbook. The workbook lives outside the repo and outside version control.
