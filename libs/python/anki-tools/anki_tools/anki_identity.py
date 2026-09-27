"""Pure module: deterministic Anki GUID and notetype-id helpers. Plain hashing
only -- no Anki imports, no filesystem access, no collection access.
"""

import hashlib

# Anki's own `anki.utils.base91`/`guid64()` alphabet, reproduced here (not
# imported) to keep this module's "no Anki imports" invariant.
GUID_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
)


def base91(num: int) -> str:
    """Encode a non-negative int in Anki's own guid64 alphabet.

    `num == 0` would encode as the empty string in a naive port; guarded
    here to return the alphabet's first character instead.
    """
    if num == 0:
        return GUID_ALPHABET[0]

    base = len(GUID_ALPHABET)
    digits: list[str] = []
    while num > 0:
        num, remainder = divmod(num, base)
        digits.append(GUID_ALPHABET[remainder])
    return "".join(reversed(digits))


def guid_for_row(russian: str, pos: str) -> str:
    """Deterministic Anki note GUID for one source row, derived from
    `russian` + `pos` only.
    """
    canonical = f"{pos}\x1f{russian}".encode()
    digest = hashlib.sha256(canonical).digest()
    num = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return base91(num)


def notetype_id_for_name(name: str) -> int:
    """Deterministic Anki notetype id for `name`, masked to 62 bits to stay
    clear of `NotetypeId`'s signed-64-bit boundary.
    """
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 62) - 1)
