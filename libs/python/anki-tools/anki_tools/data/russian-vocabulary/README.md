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

## Similarity groups and cues

`similarity-groups.tsv` lists every group of words that share an English meaning.
It is generated; regenerate it after any vocabulary change with
`uv run python -m anki_tools.collisions --write-similarity-table` (a test fails
when it is stale). Rules for the `English Distinction` cue:

- Each English meaning is its own group. A word with several meanings sits in
  several groups, across all decks and parts of speech, Mutable and Immutable.
- A word whose `told apart by` is `cue` needs a cue, even when its other
  meanings already differ from its partners'.
- A word in no group gets no cue.
- Adjective/adverb pairs need no cue: the part of speech and deck separate them.
- A cue holds only what separates the word within its groups, as short as
  possible; a word in several groups may run slightly longer.
- Partner cues must sound different from each other.
- A cue never repeats the English or the Info, never names a part of speech or a
  case, and is never "general use".
- Rare exception: a cue may reuse an English word when it names the category the
  word belongs to (e.g. "business" as the category for commerce). Use sparingly.
- Parenthetical qualifiers do not stay in the English; they move to the cue.
- Anything else about usage goes in `Additional Info`.

## Variant pairs

`variant-pairs.tsv` holds pairs of words that mean exactly the same thing and
differ only in register (пусть / пускай, чтобы / чтоб, мол / дескать). Each pair
is one note of the "Russian - Variant Pairs (Ellis Version)" note type
(`anki_tools/variant_pairs.py`): the default word, the variant and its register,
with three cards — default → English, variant → English, and English → both
words, each on its own line with its own audio. A pair belongs here only when
neither word does anything the other can't; near-synonyms with a real
difference stay as separate cards with cues.

## Build input

These TSV files are the build input for everything downstream in this package.
