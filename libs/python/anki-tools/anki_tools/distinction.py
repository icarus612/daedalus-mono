"""Two dedicated fields that tell same-looking cards apart.

Both decks contain cards that are indistinguishable from one side alone:

- the SAME Russian spelling with two parts of speech -- `как` is both a
  conjunction and an adverb, `правда` both a noun and an adverb. Seeing the
  word, there is nothing to say which card is being asked for.
- DIFFERENT Russian words with the SAME English sense -- 143 senses in these
  decks are produced by two or more words. "about" is `о / об` and `насчёт`;
  "which" is `какой` and `который`. Seeing the gloss, there is nothing to
  choose by.

These are two separate problems on two separate sides, so they get two
separate fields rather than one shared one. A single field cannot hold both:
a card can need a Russian-side marker, an English-side marker, both, or
neither, and the two are edited independently.

`Russian Distinction` supersedes the editorial parenthetical currently baked
into the `Russian` TEXT ("как (conjunction)"). Text was the wrong home for
it: `guid_for_row` hashes that text and `build_filename` derives media names
from it, which is why `audio_naming.strip_qualifier` had to exist at all.
Held in its own field, it stops being load-bearing.

Pure text -- no Anki imports.
"""

RUSSIAN_FIELD = "Russian Distinction"
ENGLISH_FIELD = "English Distinction"

# Both render through the same grey-parenthetical treatment, each beside the
# side it belongs to. Appended in field order after the existing fields so a
# re-import matches them by NAME (see `immutable_words.clone_note_type` on
# why appended fields pin `id` to None).
FIELDS = (RUSSIAN_FIELD, ENGLISH_FIELD)


def qualifier_of(text: str) -> str:
    """The editorial parenthetical in a headword, without its brackets.

    `"как (conjunction)"` -> `"conjunction"`, `"дом"` -> `""`. This is the
    inverse of `audio_naming.strip_qualifier`, which returns the word
    without it; together they split a stored headword into the two things
    it has always been carrying at once.
    """
    match = _QUALIFIER.search(text or "")
    return match.group(1).strip() if match else ""


_QUALIFIER = __import__("re").compile(r"\(([^()]*)\)\s*$")

# Keyed by the `Russian` text as stored, qualifier included. A cue never names
# a case; values follow `qualifier-classification.tsv`.
ENGLISH_DISTINCTIONS: dict[str, str] = {
    "-то": "indefinite",
    "адрес": "the postal kind",
    "банк": "the financial one",
    "банкомат": "cash machine",
    "бегать": "habitually, round trips",
    "бедно": "in poverty",
    "бизнес": "commerce",
    "богато": "looking expensive",
    "ботинок": "ankle-height",
    "брать": "take hold of",
    "бронь": "for a place or event",
    "бы": "forms the conditional",
    "в / во": "inside",
    "ваш": "possessive (2nd pl./formal)",
    "везти": "by vehicle, one way",
    "вести": "on foot, one way",
    "весь": "determinative",
    "вовсе": "only with a negative: not at all",
    "водитель": "the one driving",
    "водить": "drive a car, habitually",
    "возить": "carry someone, habitually",
    "возле": "right beside",
    "возможно": "weighing the odds",
    "возраст": "how old someone is",
    "вокруг": "all the way round",
    "волос": "a single hair",
    "вон": "pointing out",
    "врач": "the medical profession",
    "время": "time in general",
    "вспоминать": "bring to mind",
    "встреча": "any meeting",
    "встречать": "encounter someone; run into someone",
    "встречаться": "one another; each other; also to date",
    "второй": "2nd in order; declines like an adjective",
    "вы": "plural / formal singular; personal (2nd pl./formal)",
    "высоко": "up",
    "где": "at",
    "говорить": "the general verb",
    "горячий": "to the touch",
    "гостиница": "the ordinary Russian word",
    "готовить": "prepare, incl. food",
    "готовиться": "oneself; get yourself ready",
    "грустно": "I feel sad",
    "грязно": "it's dirty here",
    "да": "can also act as emphasis",
    "для": "intended for",
    "для того, чтобы": "the emphatic, two-part form",
    "до того, как": "doing something",
    "добрый": "kind-hearted",
    "доктор": "as a title or form of address",
    "дорого": "it costs a lot",
    "друг": "male",
    "дёшево": "it costs little",
    "единственный": "the one and only",
    "ездить": "by vehicle, habitually",
    "если": "conditional",
    "ехать": "by vehicle, one way",
    "жаркий": "weather",
    "жарко": "weather",
    "задавать": "set a question or task",
    "закон": "a statute",
    "замечательно": "remarkably",
    "замечательный": "remarkable",
    "занятой": "of a person",
    "здесь": "static location",
    "здравствуйте": "formal",
    "знаменитый": "celebrated",
    "и": "standard",
    "идти": "on foot, one way",
    "известный": "widely known",
    "или": "plain or",
    "иметь": "the verb (bookish)",
    "интересно": "I'm curious",
    "какой": "interrogative / exclamative",
    "кино": "cinema, or film as a medium",
    "когда (adverb)": "asking a time",
    "контракт": "the formal document",
    "короткий": "not long",
    "коротко": "briefly, in speech",
    "который": "relative / interrogative",
    "кошка": "female",
    "кто": "interrogative / relative",
    "куда": "destination",
    "лампа": "a free-standing lamp",
    "лгать": "tell lies; tell untruths",
    "левый": "side",
    "лежать": "be lying down",
    "летать": "habitually, round trips",
    "лететь": "one way",
    "линия": "a geometric line",
    "ложь": "an untruth",
    "любить": "you do the liking",
    "люди": "persons, individuals",
    "мало": "not much",
    "менеджер": "a business manager",
    "метод": "a formal method",
    "мечта": "aspiration",
    "мечтать": "to aspire",
    "мимо": "going past",
    "молодо": "looking",
    "мочь": "be in a position to",
    "муха": "the insect",
    "на": "on a surface",
    "нация": "a nation state",
    "начинать": "begin an action",
    "нести": "on foot, one way",
    "неужели": "strong surprise",
    "ничего": "nothing; also 'it's fine'",
    "ничто": "not a single thing; negative",
    "но": "direct contrast",
    "носить": "habitually, round trips",
    "ну и": "emphasis",
    "огонь": "fire as such",
    "около": "near or approximately",
    "оно": "neuter",
    "опять": "the same action repeating",
    "оставаться": "remain behind",
    "останавливать": "stop something else",
    "останавливаться": "come to a halt, or lodge",
    "остановка": "bus/tram",
    "отель": "borrowed term, usually upscale/international",
    "оттого что": "less common",
    "офис": "a workplace",
    "пенальти": "in sports",
    "перед тем, как": "doing something",
    "пианино": "upright",
    "плавать": "habitually, round trips",
    "плачущий": "describing someone",
    "плыть": "one way",
    "по-другому": "conversational",
    "по-разному": "in various ways",
    "повар": "the person",
    "поднимать": "lift physically",
    "подруга": "female",
    "пожар": "blaze",
    "последний": "final in a series",
    "потому что": "the usual because",
    "почему": "cause",
    "правда (adverb)": "asserts the whole clause",
    "правый": "side",
    "приезжать": "by vehicle",
    "признавать": "acknowledge",
    "просить": "ask for something",
    "просто (adverb)": "manner: simply",
    "просто (particle)": "plays it down",
    "прохладно": "it is cool out",
    "пугаться": "become frightened",
    "пусть / пускай": 'as in "let them"',
    "путь": "a route",
    "пюре": "often mashed potatoes",
    "разве": "implies doubt",
    "разум": "the faculty of reason",
    "рассказывать": "recount at length",
    "с тех пор, как": "the time that",
    "сам": "emphatic: myself, yourself, himself...",
    "сапог": "tall",
    "свет": "illumination",
    "свидание": "romantic",
    "свой": "reflexive possessive",
    "себя": "reflexive",
    "секрет": "a kept secret",
    "секунда": "the unit of time",
    "сидеть": "be seated",
    "синий": "dark",
    "сквозь": "through something dense",
    "скучно": "I'm bored",
    "слеза": "crying",
    "слишком": "excessively",
    "сложно": "it's hard to do",
    "случай": "an instance",
    "случаться": "come to pass",
    "смешно": "it's funny",
    "согласно (preposition)": "formal",
    "спрашивать": "a question",
    "стакан": "drinking",
    "стекло": "material",
    "стоять": "be standing",
    "страшно": "frighteningly",
    "студент": "university",
    "сюда": "destination",
    "такой": "such a, so + adj.",
    "твой": "possessive (2nd sg.)",
    "тепло": "it is warm out",
    "то есть": "i.e.",
    "то... то...": "alternating",
    "товар": "merchandise",
    "только": "restrictive",
    "тот": "demonstrative",
    "трудно": "it is hard to do",
    "туда": "destination",
    "тут": "casual",
    "ты": "singular, informal; personal (2nd sg.)",
    "у": "at someone's; to have",
    "узнавать": "know by sight",
    "управляющий": "the one in charge, an administrator",
    "уродливо": "it looks ugly",
    "уходить": "on foot",
    "фирма": "a company",
    "фортепиано": "the instrument in general",
    "ходить": "on foot, regularly or there and back; on foot, habitually",
    "холодно": "it is cold out",
    "хорошо": "done well",
    "целый": "entire, unbroken",
    "часы": "the timepiece",
    "через": "across, or after (time)",
    "чтобы / чтоб": "so that + past or infinitive",
    "шанс": "an opportunity",
    "шапка": "knit/winter",
    "шляпа": "brimmed",
    "это": "this is (linking word)",
}


def english_distinction(russian: str) -> str:
    """The stored English-side hint for `russian`, or "" when it has none."""
    return ENGLISH_DISTINCTIONS.get(russian, "")
