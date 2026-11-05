# Russian Vocabulary Source Data

These six TSV files are the only source of the vocabulary. They are edited
directly and tracked in git; there is no workbook and no importer, and nothing
regenerates them.

## Files

| Sheet      | File            |
| ---------- | --------------- |
| Nouns      | nouns.tsv       |
| Verbs      | verbs.tsv       |
| Adjectives | adjectives.tsv  |
| Adverbs    | adverbs.tsv     |
| Pronouns   | pronouns.tsv    |
| Numerals   | numerals.tsv    |

## Editing

Add or change rows in place. Every TSV carries an `Examples` column between
`Additional Info` and `Status`, holding standalone Russian usage phrases. New
rows are tagged `New` in the `Status` column. Pronouns and Numerals have their
own field sets (see `mutable_words_plan.py`'s `FIELD_NAMES["Pronouns"]` /
`FIELD_NAMES["Numerals"]` for the exact columns).

## Build input

These TSV files are the build input for everything downstream in this package.
