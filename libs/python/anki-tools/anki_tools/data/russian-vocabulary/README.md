# Russian Vocabulary Source Data

Exported from `russian_vocabulary.xlsx` on 2026-09-26.

## Regenerating

Run from `libs/python/anki-tools`:

```
uv run python -m anki_tools.vocabulary_source --out-dir anki_tools/data/russian-vocabulary
```

`vocabulary_source.py` only reads the `Nouns`, `Verbs`, `Adjectives` and
`Adverbs` sheets of the workbook. **The 87 base words added to cover decks
5/6's deleted pronouns, numerals, and greetings (missing-base-words,
2026-09-29) are NOT in that workbook** — they were appended by hand directly
to the TSVs below. Rerunning the command above without first adding those
rows to the workbook would silently discard them. The additions are the last
rows of each sheet, tagged `New` in the `Status` column like every other row:

| Sheet      | Rows added | Words |
| ---------- | ---------- | ----- |
| Nouns      | 13         | банкомат, бронь, имя, москва, полиция, прибытие, россия, рубль, ряд, старик, сторона, чувство, раз |
| Verbs      | 16         | бежать, быть, держать, ехать, значить, иметь, нравиться, оставить, подойти, попасть, приехать, прийтись, садиться, стать, удаться, хотеть |
| Adjectives | 11         | другой, единственный, иной, каждый, личный, лучший, общий, огромный, остальной, советский, страшный |

`тысяча` was classified as a numeral in this pass (see below) and was
deliberately NOT added to Nouns, to avoid a duplicate entry.

## Sheet → file mapping

| Sheet      | File            |
| ---------- | ---------------- |
| Nouns      | nouns.tsv        |
| Verbs      | verbs.tsv        |
| Adjectives | adjectives.tsv   |
| Adverbs    | adverbs.tsv      |
| Pronouns   | pronouns.tsv     |
| Numerals   | numerals.tsv     |

## Pronouns and Numerals are hand-authored, not exported

`pronouns.tsv` (21 rows) and `numerals.tsv` (55 rows) are new as of the
missing-base-words pass and are **not produced by `vocabulary_source.py`** —
there is no `Pronouns`/`Numerals` sheet in the workbook, and the command
above never touches these two files. Their field sets were designed from
scratch to fit what pronouns and numerals actually decline (pronoun type,
gender forms, and oblique-case forms; numeral type, case governance, gender
forms, and the genitive), rather than reusing the Nouns/Adjectives field
shapes. See `mutable_words_plan.py`'s `FIELD_NAMES["Pronouns"]` /
`FIELD_NAMES["Numerals"]` for the exact columns.

## The Examples column is hand-authored too

Every TSV carries an `Examples` column between `Additional Info` and `Status`,
holding standalone Russian usage phrases that used to sit in `English` or
`Additional Info`. The workbook has no such column, and
`vocabulary_source.py` neither reads nor writes it, so regenerating a TSV from
the workbook discards both the column and the edits that moved text out of
`English` / `Additional Info`. Re-apply them by hand after any regeneration.

## Build input

These six TSV files are the build input for everything downstream in this
package — not the original workbook. The workbook lives outside the repo and
outside version control, and does not (yet) cover Pronouns or Numerals at
all.
