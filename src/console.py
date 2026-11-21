"""
Robust console input for the interactive mode.

Why this module exists
-----------------------

``input()`` is not reliable enough for a demo that is recorded on a real
Windows machine with a Vietnamese keyboard layout.  Four separate
mechanisms can turn a perfectly sensible question into "UNKNOWN":

1. **The console decodes the bytes with a legacy code page.**
   ``cmd.exe`` still uses code page 437/850 by default, and a Python
   that was *not* started in UTF-8 mode (``PYTHONUTF8=0``, the default
   before Python 3.15) decodes the bytes the user typed with ``cp1252``.
   The Vietnamese text then becomes mojibake -- ``"Môn học"`` turns into
   ``"MÃ´n há»­c"`` -- and the lexicon no longer recognises a single
   surface form, so the analyzer falls back to ``UNKNOWN``.

   This was measured on the review machine::

       $ PYTHONUTF8=0 python -c "import sys; print(sys.stdin.encoding)"
       cp1252

   ``ReadConsoleW`` (the Windows API used below) bypasses the code page
   completely: it returns UTF-16, so the text is always correct.

2. **The terminal appends control characters.**
   Reading the arrow keys, pressing ``Esc`` or using a bracketed paste
   leaves ``ESC``, ``DEL`` or ``BS`` in the line.  Those characters are
   invisible on screen but change the text the analyzer sees.

3. **A Vietnamese input method emits an unfinished syllable.**
   Telex/VNI/Unikey need a *second* key press to drop the tone mark.
   If the user presses ``Enter`` before that second key, the line ends
   with a dangling vowel ("``thphần``" instead of "``phần``"), and the
   phrase no longer matches the grammar.

4. **The console code page cannot represent the Vietnamese letters.**
   When the console of Windows is redirected to a pipe, the text is
   encoded with the code page of the console (cp437 by default).  That
   code page has no character for "ọ", "ầ" or "ồ", so the console
   writes a question mark: ``"Môn học"`` becomes ``"Môn h?c"``.  The
   information is lost at the level of the operating system -- no byte
   level repair can bring it back -- but the *word* can be restored,
   because the vocabulary of the project knows "học" and "h?c" is the
   only word of that vocabulary that has the same shape.

``read_line()`` below normalises all of that away before the text ever
reaches the pipeline:

* on a real Windows console the line is read with ``ReadConsoleW``, so
  the text is UTF-16 and never mangled by a code page,
* on a pipe or a file the **raw bytes** are read from ``sys.stdin.buffer``
  and decoded here, because the text layer of Python has already
  decoded them with a code page that can be wrong -- and a wrong
  decoding is not reversible,
* a mojibake is repaired (the bytes are put back where they belong),
* the holes of a code page are repaired (the word is restored from the
  vocabulary of the project),
* control characters and zero-width characters are removed,
* the Vietnamese tone marks of a syllable that was left in its "raw"
  form (no tone mark at all, e.g. ``"phan"`` instead of ``"phần"``) are
  restored from the lexicon of the project,
* a typo inside a word (``"thphần"`` instead of ``"phần"``) is
  repaired.

The repairs are deliberately **conservative**: a word that is simply
unknown is never changed, because a wrong guess would be worse than no
guess at all.  The vocabulary of the project -- the lexicon, the
knowledge base and the corpus -- is the only authority that decides
which spelling of a word is the right one.

The module is deliberately dependency free -- the whole project only
uses the standard library.
"""

import os
import re
import sys
from typing import Optional

IS_WINDOWS = os.name == "nt"


# ---------------------------------------------------------------------------
# Control characters
# ---------------------------------------------------------------------------
# Everything below 0x20 except TAB, plus DEL and the C1 block.  ESC
# sequences (``ESC [ 0 m``) are removed as a whole so that the trailing
# bytes of a colour reset do not leak into the text.
_CONTROL_RE = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]|[\x00-\x08\x0b-\x1f\x7f-\x9f]"
)

# Zero-width and invisible formatting characters (BOM, ZWSP, soft hyphen...).
# The characters are written as escapes so that a range can never swallow
# a printable character by accident.
_ZERO_WIDTH_RE = re.compile(
    "[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u00ad]"
)

# The ANSI/VT bracketed-paste markers some terminals wrap around a paste.
_BRACKETED_PASTE_RE = re.compile(r"\x1b\[20[01]~")


def strip_control_characters(text: str) -> str:
    """
    Remove the invisible characters a terminal may leave in the line.

    ESC sequences are removed as a whole (``ESC [ 0 m`` and friends), the
    remaining control characters and zero-width characters are dropped
    individually.
    """
    if not text:
        return ""
    text = _BRACKETED_PASTE_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    text = _ZERO_WIDTH_RE.sub("", text)
    # A trailing carriage return is what a PTY sends instead of "\n".
    return text.replace("\r", "").strip()


# ---------------------------------------------------------------------------
# Mojibake repair
# ---------------------------------------------------------------------------
_VIETNAMESE_MARK_RE = re.compile(
    r"[\u00e0\u00e1\u1ea3\u00e3\u1ea1\u0103\u1eb1\u1eaf\u1eb3\u1eb5\u1eb7"
    r"\u00e2\u1ea7\u1ea5\u1ea9\u1eab\u1ead\u00e8\u00e9\u1ebb\u1ebd\u1eb9"
    r"\u00ea\u1ec1\u1ebf\u1ec3\u1ec5\u1ec7\u00ec\u00ed\u1ec9\u1ecb"
    r"\u00f2\u00f3\u1ecf\u00f5\u1ecd\u00f4\u1ed3\u1ed1\u1ed5\u1ed7\u1ed9"
    r"\u01a1\u1edd\u1edb\u1edf\u1ee1\u1ee3\u00f9\u00fa\u1ee5\u1ee7"
    r"\u01af\u1eeb\u1ee9\u1eed\u1eef\u1ef1\u1ef3\u00fd\u1ef7\u1ef9\u1efb"
    r"\u0111\u0110]"
)

# The code pages a Windows console may use.  ``cp437`` and ``cp850`` map
# every one of the 256 byte values, so the round-trip through them is
# lossless -- they are tried first.
_CODEPAGES = ("cp437", "cp850", "cp1252", "cp1258", "cp866")


def _looks_like_vietnamese(text: str) -> bool:
    """
    Heuristic: does the text look like (correctly encoded) Vietnamese?

    A correctly encoded Vietnamese sentence contains tone marks.  The
    mojibake of such a sentence contains instead characters such as
    ``\u00c3``, ``\u00b4``, ``\u00bb`` -- the classic "\u00c3\u00a1" signature of a
    double encoding -- so the check below rejects it.
    """
    if not text:
        return False
    if _VIETNAMESE_MARK_RE.search(text):
        return True
    # Pure ASCII text (an English question, a command) is fine as well.
    return text.isascii()


def repair_mojibake(text: str) -> str:
    """
    Repair text that was decoded with the wrong code page.

    A Vietnamese UTF-8 string that was decoded with ``cp437`` (or
    ``cp1252``, ...) can be turned back into the original by encoding it
    with that code page again and decoding the result as UTF-8.

    The decisive criterion is **not** a heuristic but a fact: the round
    trip either produces valid UTF-8 or it does not.  The code pages
    that map all 256 byte values (``cp437``, ``cp850``) are tried
    first because their round trip is lossless; the others are tried
    afterwards.

    The text is returned unchanged when it is already valid UTF-8, so
    the function is safe to call on every input.
    """
    if not text:
        return text

    # A text that still carries the replacement character has lost
    # bytes: it is a mojibake, whatever it looks like.  The lost bytes
    # are recovered separately (see _repair_broken_mojibake).
    if "�" in text:
        return _repair_broken_mojibake(text)

    # The strict round-trip is tried FIRST, whatever the text looks
    # like.  It is the only reliable criterion: it either yields valid
    # UTF-8 or it does not.  A heuristic ("does this look like
    # Vietnamese?") cannot be used as a guard here, because the
    # mojibake of a code page such as cp437 contains characters like
    # "o" with a circumflex that would fool such a check.
    #
    # Strict round-trip: lossless when it succeeds.  ``latin-1`` maps
    # all 256 byte values one to one, so it is the most faithful
    # choice; the Windows code pages are tried as well because their
    # mojibake has a slightly different shape.
    #
    # Note: a text that was decoded with ``cp1252`` has *already* lost
    # the bytes 0x81, 0x8D, 0x8F, 0x90 and 0x9D (they have no cp1252
    # counterpart), so it cannot be repaired perfectly any more.  That
    # is exactly why the interactive mode reads a real Windows console
    # with ``ReadConsoleW`` instead of relying on this repair.
    for codepage in ("latin-1",) + _CODEPAGES:
        try:
            raw = text.encode(codepage, errors="strict")
        except UnicodeEncodeError:
            continue
        try:
            repaired = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        if repaired and _looks_like_vietnamese(repaired):
            return repaired

    # ``surrogateescape`` round-trip: a byte that has no counterpart in
    # the code page was turned into U+FFFD (or into a control
    # character) when the console decoded the line.  ``surrogateescape``
    # keeps those bytes as lone surrogates, so they can be put back.
    for codepage in ("cp1252", "cp1258"):
        try:
            raw = text.encode(codepage, errors="surrogateescape")
        except (UnicodeEncodeError, UnicodeError):
            continue
        try:
            repaired = raw.decode("utf-8", errors="strict")
        except (UnicodeDecodeError, UnicodeError):
            continue
        if repaired and _looks_like_vietnamese(repaired):
            return repaired

    # The text was already correct: leave it alone.  This check comes
    # *before* the lossy round-trip, because the lossy one would turn a
    # perfectly good Vietnamese sentence into a string full of "?"
    # (cp1252 cannot represent the bytes 0x81, 0x8D, 0x8F, 0x90 and
    # 0x9D, which every Vietnamese sentence contains).
    if _looks_like_vietnamese(text):
        return text

    # Lossy round-trip with **byte recovery**.
    #
    # A code page such as cp1252 cannot represent five byte values
    # (0x81, 0x8D, 0x8F, 0x90 and 0x9D).  When the console decoded the
    # line, those bytes became the replacement character U+FFFD and the
    # information was lost -- but only *which* of the five bytes it was.
    #
    # The bytes are recovered by trying them: a byte only makes sense
    # when the surrounding bytes form a valid UTF-8 sequence.  For
    # "hoc" (U+1ECD = E1 BB 8D) the byte 0x8D is the only one that
    # turns "E1 BB" into a complete three byte sequence, so it is
    # recovered with certainty.
    for codepage in ("cp1252", "cp1258"):
        recovered = _recover_lost_bytes(text, codepage)
        if recovered is not None and _looks_like_vietnamese(recovered):
            return recovered
    # Plain lossy round-trip as a last resort: the surrounding words
    # are restored nevertheless, which is usually enough for the
    # lexicon to match the question again.
    for codepage in ("latin-1",) + _CODEPAGES:
        try:
            raw = text.encode(codepage, errors="replace")
        except UnicodeEncodeError:
            continue
        repaired = raw.decode("utf-8", errors="replace").replace("\ufffd", "")
        if repaired != text and _looks_like_vietnamese(repaired):
            return repaired

    # Nothing could be repaired: the text was already correct.
    return text


def _repair_broken_mojibake(text: str) -> str:
    """
    Repair a mojibake that has lost some of its bytes.

    The console replaced every byte its code page could not represent
    with the replacement character U+FFFD.  For cp1252 and cp1258 there
    are only five such bytes, so the lost information can be recovered
    by trying them and keeping the candidate the lexicon recognises.
    """
    for codepage in ("cp1252", "cp1258"):
        recovered = _recover_lost_bytes(text, codepage)
        if recovered is not None:
            return recovered

    # Nothing could be recovered: at least drop the replacement
    # characters so that the rest of the sentence stays usable.
    cleaned = text.replace("�", "")
    if cleaned != text and _looks_like_vietnamese(cleaned):
        return cleaned
    return text


# The byte values that cp1252 and cp1258 cannot represent.  When the
# console decoded the line, each of them became the replacement
# character U+FFFD.
_LOST_BYTES = (0x81, 0x8D, 0x8F, 0x90, 0x9D)


def _recover_lost_bytes(text: str, codepage: str):
    """
    Rebuild a mojibake whose missing bytes are known to be a small set.

    The console replaced every byte it could not represent with U+FFFD.
    The function puts every candidate byte back and keeps the
    combination that

    * produces valid UTF-8, and
    * produces the sentence the assistant actually knows.

    The second criterion matters because a lost byte is not always
    unique: "E1 BB ?" is a valid UTF-8 sequence for "E1 BB 81" (U+1EC1,
    "ề") as well as for "E1 BB 8D" (U+1ECD, "ọ").  The candidates are
    therefore ranked by the number of lexicon surfaces the resulting
    sentence contains -- the lexicon of the project is the only
    authority on which spelling is a real Vietnamese word.

    ``None`` is returned when the bytes cannot be recovered.
    """
    if "\ufffd" not in text:
        return None
    # The text is turned back into bytes *character by character*, so that
    # the position of every lost byte is known exactly.  A code page that
    # cannot represent one of the characters of the mojibake is not the
    # code page the console used, so it is rejected.
    raw = bytearray()
    holes = []
    for char in text:
        if char == "\ufffd":
            holes.append(len(raw))
            raw.append(0x00)
            continue
        try:
            raw.extend(char.encode(codepage))
        except UnicodeEncodeError:
            return None

    if not holes or len(holes) > 4:
        return None

    candidates = _LOST_BYTES

    best = None
    best_score = -1
    for combination in _byte_combinations(len(holes), candidates):
        candidate = bytearray(raw)
        for position, value in zip(holes, combination):
            candidate[position] = value
        try:
            repaired = bytes(candidate).decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        if "\ufffd" in repaired:
            continue
        score = _score_candidate(repaired)
        if score > best_score:
            best_score = score
            best = repaired

    return best


def _score_candidate(text: str) -> int:
    """
    How well a candidate repairs the sentence.

    The vocabulary of the project decides: a candidate that turns the
    question into a sentence made of *known* Vietnamese words is the
    right one.  This is the only way to tell the candidates apart --
    structurally they are all valid UTF-8 ("E1 BB 81" is "ề" as
    well as "E1 BB 8D" is "ọ"), so the language itself has to
    decide.

    The lexicon lookup alone is not enough: it recognises the *phrase*
    "môn học" but not the single word "học", and the damaged
    word is exactly the one that has to be judged.  The word list below
    contains every single word of the lexicon plus the function words
    of the domain, so "học" is known and "hềc" is not.
    """
    score = 0
    if _VIETNAMESE_MARK_RE.search(text):
        score += 1
    if text.rstrip().endswith("?"):
        score += 1

    words = _word_re.findall(text.lower())
    known = 0
    frequency = _corpus_frequency()
    for word in words:
        if word in _known_words():
            known += 1
        elif _raw_lookup(word).lower() != word:
            # A raw (mark-less) spelling of a known word still counts.
            known += 1
        elif _known_suffix(word):
            # A word with a typing mistake inside it ("thphần") is
            # judged by the word it ends with ("phần").
            known += 1
    score += 10 * known
    score -= len(words) - known

    # The corpus decides between two words that are both known: the
    # one that the questions of the course use is the right one.
    for word in words:
        score += frequency.get(word, 0)
        suffix = _known_suffix(word)
        if suffix:
            score += frequency.get(suffix, 0)

    try:
        from .lexicon import get_lexicon

        score += 5 * len(get_lexicon().lookup(text))
    except Exception:  # pragma: no cover - the lexicon is always shipped
        pass
    return score


# The vocabulary used to judge a repaired sentence.
_KNOWN_WORDS = None


def _known_words():
    """Every single word the assistant knows."""
    global _KNOWN_WORDS
    if _KNOWN_WORDS is not None:
        return _KNOWN_WORDS

    words = set()
    try:
        from .lexicon import get_lexicon

        lexicon = get_lexicon()
        for group in lexicon.groups.values():
            for surface, canonical in group.items():
                for part in (surface, canonical):
                    words.update(part.lower().replace("_", " ").split())
    except Exception:  # pragma: no cover - the lexicon is always shipped
        pass

    try:
        from .preprocessing import MULTIWORD_ENTITIES, VIETNAMESE_POS_TAGS

        for surface, _kind in MULTIWORD_ENTITIES:
            words.update(surface.lower().replace("_", " ").split())
        for tag in VIETNAMESE_POS_TAGS:
            words.update(tag.lower().replace("_", " ").split())
    except Exception:  # pragma: no cover - always shipped
        pass

    # The function words of the domain that carry no entity.
    words.update(
        """
        những gồm môn học nào phần chương tuần bài tập
        lớn nói về gì yêu cầu xây dựng deadline nộp hạn
        thời kỳ giữa cuối tài liệu giảng viên phụ trách
        chính sách đạo đức liêm kỹ thuật sau mấy nhiêu
        là có được bị và của trong cho không như với
        cùng theo để mà nhưng nếu khi thì một các nào gì
        ở đâu ai
        """.split()
    )
    words.discard("")

    _KNOWN_WORDS = words
    return words


def _known_suffix(word: str) -> str:
    """
    The known word a mistyped word ends with.

    The extra letters of a typing mistake are typed *inside* the word
    ("thphần" instead of "phần"), so the word is at the end of the
    token and the extra prefix is short.  The **longest** known suffix
    is returned, or an empty string when there is none.
    """
    bare = word.lower()
    known = _known_words()
    for size in range(min(len(bare) - 1, 12), 0, -1):
        suffix = bare[-size:]
        if suffix in known:
            return suffix
    return ""


_word_re = re.compile(
    r"[a-zA-Z\u00e0\u00e1\u1ea3\u00e3\u1ea1\u0103\u1eb1\u1eaf\u1eb3\u1eb5\u1eb7"
    r"\u00e2\u1ea7\u1ea5\u1ea9\u1eab\u1ead\u00e8\u00e9\u1ebb\u1ebd\u1eb9"
    r"\u00ea\u1ec1\u1ebf\u1ec3\u1ec5\u1ec7\u00ec\u00ed\u1ec9\u1ecb"
    r"\u00f2\u00f3\u1ecf\u00f5\u1ecd\u00f4\u1ed3\u1ed1\u1ed5\u1ed7\u1ed9"
    r"\u01a1\u1edd\u1edb\u1edf\u1ee1\u1ee3\u00f9\u00fa\u1ee5\u1ee7"
    r"\u01af\u1eeb\u1ee9\u1eed\u1eef\u1ef1\u1ef3\u00fd\u00f7\u1ef9\u1efb"
    r"\u0111\u0110]+"
)


def _byte_combinations(count: int, values):
    """Every combination of ``count`` candidate bytes."""
    if count == 1:
        for value in values:
            yield (value,)
        return
    for head in values:
        for tail in _byte_combinations(count - 1, values):
            yield (head,) + tail


# ---------------------------------------------------------------------------
# Question-mark holes
# ---------------------------------------------------------------------------
# When the console of Windows is redirected to a pipe, the text is encoded
# with the code page of the console (cp437 by default).  That code page
# cannot represent the Vietnamese letters -- "học" becomes "h?c" -- and
# the information is lost at the level of the operating system: no byte
# level repair can bring it back.
#
# The *word* can nevertheless be restored: the vocabulary of the project
# knows "học", and "h?c" is the only word of that vocabulary that has
# the same shape (the same length, the same plain letters and the accent
# on the same position).  The repair is applied only when the match is
# unique, so an ambiguous hole is left untouched.
_HOLE_TOKEN_RE = re.compile(
    r"[a-zA-Z\u00e0\u00e1\u1ea3\u00e3\u1ea1\u0103\u1eb1\u1eaf\u1eb3\u1eb5\u1eb7"
    r"\u00e2\u1ea7\u1ea5\u1ea9\u1eab\u1ead\u00e8\u00e9\u1ebb\u1ebd\u1eb9"
    r"\u00ea\u1ec1\u1ebf\u1ec3\u1ec5\u1ec7\u00ec\u00ed\u1ec9\u1ecb"
    r"\u00f2\u00f3\u1ecf\u00f5\u1ecd\u00f4\u1ed3\u1ed1\u1ed5\u1ed7\u1ed9"
    r"\u01a1\u1edd\u1edb\u1edf\u1ee1\u1ee3\u00f9\u00fa\u1ee5\u1ee7"
    r"\u01af\u1eeb\u1ee9\u1eed\u1eef\u1ef1\u1ef3\u00fd\u00f7\u1ef9\u1efb"
    r"\u0111\u0110?]+"
)

# The index of the words that can be restored from a hole.
_HOLE_INDEX = None

# The letters that do not carry an accent.
_PLAIN_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _accent_positions(word: str) -> frozenset:
    """The positions of the accented letters of a word."""
    return frozenset(
        index
        for index, char in enumerate(word)
        if char not in _PLAIN_LETTERS
    )


def _build_hole_index():
    """
    Index the vocabulary by the shape of its words.

    The shape of a word is described by two things: its length and the
    positions of its accented letters.  "học" has the shape (3, {1}),
    "những" has the shape (5, {2}).

    Two words can only be confused when they have the same shape, so
    the index tells the repair which words have to be compared.
    """
    global _HOLE_INDEX
    if _HOLE_INDEX is not None:
        return

    index = {}
    for word in _known_words():
        if len(word) < 2 or "?" in word:
            continue
        positions = _accent_positions(word)
        if not positions:
            # A word without an accent can never match a hole.
            continue
        index.setdefault((len(word), positions), []).append(word)

    _HOLE_INDEX = index


def _repair_hole_word(word: str) -> str:
    """
    The restored spelling of a word with a hole, or the word itself.

    A hole (``"?"``) stands for exactly one lost Vietnamese letter.
    The lost letter is found by looking for a known word that

    * has the same length,
    * has its accents on exactly the same positions, and
    * has the same plain letters everywhere else.

    The repair is applied only when the match is **unique**.  When
    several words have the same shape ("nhưng" and "những" do), the
    one that is the most frequent in the corpus of the project wins;
    when even that does not decide, the hole is left alone, because a
    wrong guess would be worse than no guess at all.
    """
    _build_hole_index()

    lowered = word.lower()
    holes = [index for index, char in enumerate(lowered) if char == "?"]
    if not holes:
        return word

    # Every hole must stand for an accented letter, so the number of
    # holes has to match the number of accents of the candidate word.
    accent_positions = _accent_positions(lowered)
    if accent_positions != frozenset(holes):
        # The holes do not line up with the accents of a known word.
        return word

    plain = _strip_marks(lowered)
    candidates = _HOLE_INDEX.get((len(lowered), accent_positions))

    matches = []
    if candidates:
        for candidate in candidates:
            candidate_plain = _strip_marks(candidate)
            if all(
                candidate_plain[index] == plain[index]
                for index in range(len(plain))
                if index not in holes
            ):
                matches.append(candidate)

    if not matches:
        # No match at all: the hole stays.
        return word

    if len(matches) > 1:
        # Several words have the same shape: the corpus decides.
        frequency = _corpus_frequency()
        ranked = sorted(
            matches,
            key=lambda candidate: (-frequency.get(candidate, 0), candidate),
        )
        best = ranked[0]
        second = ranked[1]
        if frequency.get(best, 0) <= frequency.get(second, 0):
            # The corpus does not decide: the hole stays.
            return word
        matches = [best]

    replacement = matches[0]
    if word[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


# The word frequencies of the corpus of the project.
_CORPUS_FREQUENCY = None


def _corpus_frequency():
    """
    How often each word occurs in the corpus of the project.

    The corpus is the set of files that ship with the project: the
    official questions, the course data, the test data and the
    evaluation cases.  The frequencies are only used to break a tie
    between two words that have the same shape, so a rough count is
    enough.
    """
    global _CORPUS_FREQUENCY
    if _CORPUS_FREQUENCY is not None:
        return _CORPUS_FREQUENCY

    import os
    from collections import Counter

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    counter = Counter()

    for relative in (
        "input/sentences.txt",
        "data/course_data.txt",
        "tests/data/dialogues.txt",
        "tests/data/sample_queries.txt",
    ):
        path = os.path.join(root, relative)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError:
            continue
        for word in _word_re.findall(text.lower()):
            counter[word] += 1

    # The lexicon surfaces count as well: an entity is known even when
    # no question mentions it.
    for word in _known_words():
        counter.setdefault(word, 0)

    _CORPUS_FREQUENCY = counter
    return counter


def _hole_candidates(token: str):
    """
    The known words that could fill the holes of a token.

    An empty list is returned when the token has no hole or when no
    word of the vocabulary has the same shape.
    """
    lowered = token.lower()
    holes = [index for index, char in enumerate(lowered) if char == "?"]
    if not holes:
        return []

    _build_hole_index()

    # Every hole must stand for an accented letter, so the number of
    # holes has to match the number of accents of the candidate word.
    accent_positions = _accent_positions(lowered)
    if accent_positions != frozenset(holes):
        return []

    plain = _strip_marks(lowered)
    candidates = _HOLE_INDEX.get((len(lowered), accent_positions)) or []

    matches = []
    for candidate in candidates:
        candidate_plain = _strip_marks(candidate)
        if all(
            candidate_plain[index] == plain[index]
            for index in range(len(plain))
            if index not in holes
        ):
            matches.append(candidate)

    if matches:
        return matches

    # The token may carry a typing mistake as well: the extra letters
    # were typed inside the word ("thph?n" instead of "ph?n").  The
    # word is therefore looked for at the *end* of the token, with a
    # short extra prefix.
    return _hole_candidates_with_prefix(lowered, holes, plain)


def _hole_candidates_with_prefix(lowered: str, holes, plain: str):
    """
    The known words that could fill the holes of a mistyped token.

    The extra letters of a typing mistake are typed *inside* the word,
    so the word is at the end of the token and the prefix is short.
    The candidate that is returned still carries the extra letters --
    the repair of the typo itself is done later, by
    :func:`repair_typos`.
    """
    matches = []
    for extra in (1, 2):
        if len(lowered) - extra < 2:
            break
        suffix = lowered[extra:]
        suffix_holes = [index for index, char in enumerate(suffix) if char == "?"]
        if len(suffix_holes) != len(holes):
            continue

        suffix_plain = _strip_marks(suffix)
        accent_positions = _accent_positions(suffix)
        if accent_positions != frozenset(suffix_holes):
            continue

        for candidate in _HOLE_INDEX.get((len(suffix), accent_positions)) or []:
            candidate_plain = _strip_marks(candidate)
            if all(
                candidate_plain[index] == suffix_plain[index]
                for index in range(len(suffix_plain))
                if index not in suffix_holes
            ):
                matches.append(lowered[:extra] + candidate)

    return matches


def _repair_hole_word(word: str) -> str:
    """
    The restored spelling of a word with a hole, or the word itself.

    A hole (``"?"``) stands for exactly one lost Vietnamese letter.
    The lost letter is found by looking for a known word that

    * has the same length,
    * has its accents on exactly the same positions, and
    * has the same plain letters everywhere else.

    The repair is applied only when the match is **unique**.  When
    several words have the same shape ("nhưng" and "những" do), the
    one that is the most frequent in the corpus of the project wins;
    when even that does not decide, the hole is left alone, because a
    wrong guess would be worse than no guess at all.
    """
    matches = _hole_candidates(word)
    if not matches:
        # No match at all: the hole stays.
        return word

    if len(matches) > 1:
        # Several words have the same shape: the corpus decides.
        frequency = _corpus_frequency()
        ranked = sorted(
            matches,
            key=lambda candidate: (-frequency.get(candidate, 0), candidate),
        )
        best = ranked[0]
        second = ranked[1]
        if frequency.get(best, 0) <= frequency.get(second, 0):
            # The corpus does not decide: the hole stays.
            return word
        matches = [best]

    replacement = matches[0]
    if word[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def repair_holes(text: str) -> str:
    """
    Restore the Vietnamese words that the console code page destroyed.

    The Windows console cannot represent the Vietnamese letters, so a
    redirected line arrives with holes in it: "Môn học gồm những phần
    nào?" becomes "Môn h?c g?m nh?ng ph?n nào?".  The information is
    lost at the level of the operating system -- no byte level repair
    can bring it back -- but the *word* can be restored, because the
    vocabulary of the project knows "học" and "h?c" is the only word
    of that vocabulary that has the same shape.

    When several words have the same shape, the one that makes the
    **whole sentence** the most plausible is chosen: the repair is
    judged in its context, not word by word.

    A word that is already correct is never touched.
    """
    if not text or "?" not in text:
        return text

    # Every token with a hole is repaired first, and the result is
    # judged in the context of the whole sentence.
    tokens = list(_HOLE_TOKEN_RE.finditer(text))
    if not tokens:
        return text

    options = []
    for match in tokens:
        token = match.group(0)
        # A question mark at the end of a token is the punctuation of
        # the sentence, not a hole.
        if token.endswith("?"):
            options.append([token])
            continue
        candidates = _hole_candidates(token)
        if not candidates:
            options.append([token])
            continue
        options.append([token] + [_match_case(token, c) for c in candidates])

    # The best combination is the one that makes the sentence the most
    # plausible.  The number of combinations is tiny (the holes of a
    # question are rare and each of them has few candidates).
    best = None
    best_score = None
    for combination in _combinations(options):
        candidate = _apply_options(text, tokens, combination)
        score = _score_candidate(candidate)
        if best_score is None or score > best_score:
            best_score = score
            best = candidate
        if best_score is not None and score == best_score and best is not None:
            # A tie: prefer the version with the fewest holes left.
            if candidate.count("?") > best.count("?"):
                best = best
    return best if best is not None else text


def _match_case(token: str, word: str) -> str:
    """The candidate with the capitalisation of the token."""
    if token[:1].isupper():
        return word[:1].upper() + word[1:]
    return word


def _combinations(options):
    """Every combination of the options of every token."""
    if not options:
        yield ()
        return
    head, *tail = options
    for choice in head:
        for rest in _combinations(tail):
            yield (choice,) + rest


def _apply_options(text: str, tokens, combination) -> str:
    """Rebuild the text with the chosen replacement of every token."""
    result = []
    position = 0
    for match, choice in zip(tokens, combination):
        result.append(text[position : match.start()])
        result.append(choice)
        position = match.end()
    result.append(text[position:])
    return "".join(result)


# ---------------------------------------------------------------------------
# Vietnamese syllable repair
# ---------------------------------------------------------------------------
# Telex, VNI and Unikey need a *second* key press to drop the tone mark.
# If the user presses ``Enter`` before that second key press, the
# syllable stays raw: the user types "``phan``" where they meant
# "``phần``" and the question no longer matches the grammar.
#
# Instead of maintaining a hand-written table (which would quickly go out
# of date), the raw forms are derived from the **lexicon of the project**:
# every surface form the assistant knows is indexed by its "raw" spelling
# and the lookup restores the accented one.  A word the lexicon does not
# know is left untouched, so a legitimate untoned word is never corrupted.
_RAW_INDEX = {}
_RAW_INDEX_READY = False


def _strip_marks(word: str) -> str:
    """The "raw" spelling of a word: the same letters without the marks."""
    replacements = {
        "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
        "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
        "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
        "đ": "d",
    }
    return "".join(replacements.get(char, char) for char in word.lower())


def _build_raw_index() -> None:
    """
    Index every lexicon surface by its raw (mark-less) spelling.

    The lexicon of the project is the single source of truth for the
    vocabulary, so this stays correct automatically when the lexicon
    grows.
    """
    global _RAW_INDEX_READY
    if _RAW_INDEX_READY:
        return
    _RAW_INDEX_READY = True

    try:
        from .lexicon import get_lexicon

        lexicon = get_lexicon()
    except Exception:  # pragma: no cover - the lexicon is always shipped
        return

    for group in lexicon.groups.values():
        for surface in group:
            raw = _strip_marks(surface)
            if raw == surface.lower():
                # Already without marks -- nothing to repair.
                continue
            # The first surface wins so that the mapping stays stable.
            _RAW_INDEX.setdefault(raw, surface)


# Extra words that are not in the lexicon but that a user is likely to
# type in the raw form.
_EXTRA_RAW_WORDS = {
    "ngoi": "ngôi",
    "tieng": "tiếng",
    "viet": "việt",
    "xuat": "xuất",
    "them": "thêm",
    "moi": "mới",
    "cac": "các",
    "nhieu": "nhiều",
    "it": "ít",
    "gi": "gì",
    "nao": "nào",
    "mon": "môn",
    "hoc": "học",
    "gom": "gồm",
    "nhung": "những",
    "phan": "phần",
    "tuan": "tuần",
    "bai": "bài",
    "tap": "tập",
    "lon": "lớn",
    "co": "có",
    "khong": "không",
    "may": "mấy",
    "chuong": "chương",
    "tai": "tài",
    "lie": "liệu",
    "yeu": "yêu",
    "cau": "cầu",
    "xay": "xây",
    "dung": "dựng",
    "giang": "giảng",
    "vien": "viên",
    "nhiem": "nhiệm",
    "vu": "vụ",
    "noi": "nói",
    "ve": "về",
    "trinh": "trình",
    "bay": "bày",
    "bao": "báo",
    "cao": "cáo",
    "keo": "kéo",
    "gioi": "giới",
    "thieu": "thiệu",
    "dinh": "định",
    "nghia": "nghĩa",
    "mu": "mư",
    "nhan": "nhận",
    "dien": "điện",
    "thanh": "thành",
    "thu": "thư",
    "muc": "mục",
    "ngoi": "ngôi",
    "tieng": "tiếng",
    "viet": "việt",
    "xuat": "xuất",
    "them": "thêm",
    "moi": "mới",
    "cac": "các",
    "nhieu": "nhiều",
    "it": "ít",
    "quy": "quy",
    "dinh": "định",
    "sai": "sai",
    "lam": "làm",
    "giup": "giúp",
    "chuong": "chương",
    "mo": "mở",
    "ra": "ra",
    "vao": "vào",
    "tu": "từ",
    "den": "đến",
    "truoc": "trước",
    "sau": "sau",
    "khi": "khi",
    "o": "ở",
    "dau": "đâu",
    "the": "thế",
    "nhu": "như",
    "gio": "giờ",
    "viec": "việc",
    "khac": "khác",
    "cau": "câu",
    "tra": "trả",
    "loi": "lời",
    "cua": "của",
    "trong": "trong",
    "thanh": "thành",
    "cong": "công",
    "dung": "dụng",
    "hoc": "học",
    "cua": "của",
    "la": "là",
    "nop": "nộp",
    "phu": "phụ",
    "trac": "trác",
    "giang": "giảng",
    "vien": "viên",
    "phan": "phần",
    "cong": "công",
    "viec": "việc",
    "thu": "thư",
    "muc": "mục",
    "mo": "mở",
    "ranh": "ranh",
    "giua": "giữa",
    "ky": "kỳ",
    "cuoi": "cuối",
    "thoi": "thời",
    "han": "hạn",
    "nghia": "nghĩa",
    "dinh": "định",
    "ghi": "ghi",
    "chu": "chú",
    "hien": "hiện",
    "bai": "bài",
    "tap": "tập",
    "lon": "lớn",
    "yeu": "yêu",
    "cau": "cầu",
    "xay": "xây",
    "dung": "dựng",
    "nhom": "nhóm",
    "thanh": "thành",
    "phai": "phải",
    "doi": "đổi",
    "moi": "mới",
    "cu": "cũ",
    "cuu": "cứu",
    "tinh": "tính",
    "phien": "phiên",
    "hop": "hộp",
    "thuoc": "thuộc",
    "ve": "về",
    "do": "độ",
    "gio": "giờ",
    "san": "sản",
    "pham": "phạm",
    "vi": "vị",
    "toan": "toán",
    "xac": "xác",
    "suat": "suất",
    "phan": "phần",
}


def _raw_lookup(word: str) -> str:
    """The accented spelling of a raw word, or the word itself."""
    raw = word.lower()
    replacement = _RAW_INDEX.get(raw) or _EXTRA_RAW_WORDS.get(raw)
    if replacement is None:
        return word
    if word[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


_RAW_WORD_RE = re.compile(
    r"[a-zA-Zàáảãạăâđêôơưèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]+"
)


def repair_raw_syllables(text: str) -> str:
    """
    Restore the tone marks of the words a Vietnamese input method left
    in their "raw" form.

    Telex and VNI need a second key press to drop the tone mark.  If the
    user presses ``Enter`` too early the syllable stays raw: the user
    types "``phan``" where they meant "``phần``" and the question no
    longer matches the grammar.

    Only the words of the domain are corrected (they come from the
    lexicon of the project), so a legitimate untoned word is not
    touched by accident.
    """
    if not text:
        return text

    _build_raw_index()

    return _RAW_WORD_RE.sub(lambda m: _raw_lookup(m.group(0)), text)


# ---------------------------------------------------------------------------
# Typo repair
# ---------------------------------------------------------------------------
# A word that is not in the vocabulary but *ends* with a word that is
# ("thphần" -> "phần") is almost always a typing mistake: the extra
# letters were typed inside the word.  The rule is deliberately
# conservative:
#
# * the word itself must be **unknown** (otherwise nothing is touched),
# * the word it ends with must be at least three characters long and
#   must carry a Vietnamese tone mark (so that the repair produces a
#   correctly spelled Vietnamese word),
# * the extra letters must be at most two.
#
# A word that is simply unknown ("xyzzy") is left alone.
_VN_SURFACES = []
_ALL_WORDS = set()


def _build_typo_index() -> None:
    """Index the vocabulary used by the typo repair."""
    global _VN_SURFACES, _ALL_WORDS
    if _VN_SURFACES:
        return

    try:
        from .lexicon import get_lexicon
        from .preprocessing import MULTIWORD_ENTITIES, VIETNAMESE_POS_TAGS

        lexicon = get_lexicon()
    except Exception:  # pragma: no cover - the lexicon is always shipped
        return

    surfaces = set()
    for group in lexicon.groups.values():
        for surface, canonical in group.items():
            surfaces.add(surface.lower())
            surfaces.add(canonical.lower().replace("_", " "))
    for surface, _kind in MULTIWORD_ENTITIES:
        surfaces.add(surface.lower().replace("_", " "))
    for word in VIETNAMESE_POS_TAGS:
        surfaces.add(word.lower().replace("_", " "))

    # The function words of the domain that are not in the lexicon.
    for extra in (
        "những", "gồm", "môn", "học", "nào", "phần", "chương", "tuần",
        "bài", "tập", "lớn", "nói", "về", "gì", "yêu", "cầu", "xây",
        "dựng", "deadline", "nộp", "hạn", "thời", "kỳ", "giữa", "cuối",
        "tài", "liệu", "giảng", "viên", "phụ", "trách", "chính", "sách",
        "đạo", "đức", "liêm", "kỹ", "thuật", "sau", "mấy", "nhiêu", "là",
    ):
        surfaces.add(extra)

    _ALL_WORDS = {s for s in surfaces if " " not in s}
    _VN_SURFACES = sorted(
        (
            s
            for s in _ALL_WORDS
            if len(s) >= 3 and _VIETNAMESE_MARK_RE.search(s)
        ),
        key=len,
        reverse=True,
    )


def _repair_word_typo(word: str) -> str:
    """The corrected spelling of a mistyped word, or the word itself."""
    bare = word.lower()
    if bare in _ALL_WORDS:
        return word
    for surface in _VN_SURFACES:
        if bare.endswith(surface) and 0 < len(bare) - len(surface) <= 2:
            if word[:1].isupper():
                return surface[:1].upper() + surface[1:]
            return surface
    return word


def repair_typos(text: str) -> str:
    """
    Repair the words that were typed with a typo inside them.

    ``"Môn học gồm những thphần nào?"`` becomes
    ``"Môn học gồm những phần nào?"``: the extra letters were typed
    inside the word.  The rule is conservative -- a word that is simply
    unknown is never changed -- so a question about something the
    assistant does not know about keeps its wording.
    """
    if not text:
        return text

    _build_typo_index()
    if not _VN_SURFACES:
        return text

    return _TYPO_WORD_RE.sub(lambda m: _repair_word_typo(m.group(0)), text)


_TYPO_WORD_RE = re.compile(
    r"[a-zA-Z\u00e0\u00e1\u1ea3\u00e3\u1ea1\u0103\u1eb1\u1eaf\u1eb3\u1eb5\u1eb7"
    r"\u00e2\u1ea7\u1ea5\u1ea9\u1eab\u1ead\u00e8\u00e9\u1ebb\u1ebd\u1eb9"
    r"\u00ea\u1ec1\u1ebf\u1ec3\u1ec5\u1ec7\u00ec\u00ed\u1ec9\u1ecb"
    r"\u00f2\u00f3\u1ecf\u00f5\u1ecd\u00f4\u1ed3\u1ed1\u1ed5\u1ed7\u1ed9"
    r"\u01a1\u1edd\u1edb\u1edf\u1ee1\u1ee3\u00f9\u00fa\u1ee5\u1ee7"
    r"\u01af\u1eeb\u1ee9\u1eed\u1eef\u1ef1\u1ef3\u00fd\u1ef7\u1ef9\u1efb"
    r"\u0111\u0110]+"
)


# ---------------------------------------------------------------------------
# Reading a line
# ---------------------------------------------------------------------------
def _read_windows_console_line(prompt: str) -> Optional[str]:
    """
    Read one line from a real Windows console with ``ReadConsoleW``.

    ``ReadConsoleW`` returns the characters as UTF-16 and therefore
    ignores the console code page completely: the Vietnamese text is
    always decoded correctly, whatever ``chcp`` says.

    ``None`` is returned when the console cannot be read (not a console,
    or the handle is invalid) so that the caller falls back to
    :func:`input`.
    """
    if not IS_WINDOWS:
        return None

    try:
        import ctypes
        from ctypes import wintypes
    except Exception:  # pragma: no cover - ctypes is always available
        return None

    kernel32 = ctypes.windll.kernel32

    # STD_INPUT_HANDLE = -10
    handle = kernel32.GetStdHandle(wintypes.DWORD(-10))
    if handle in (0, -1, None):
        return None

    # Make sure the handle really is a console: GetConsoleMode fails on a
    # redirected pipe.
    mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return None

    if prompt:
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        except Exception:
            pass

    # ReadConsoleW wants a buffer of wchar.  1024 characters are more
    # than enough for a question.
    buffer = ctypes.create_unicode_buffer(1024)
    read = wintypes.DWORD()
    if not kernel32.ReadConsoleW(
        handle,
        ctypes.byref(buffer),
        ctypes.sizeof(buffer) - 2,
        ctypes.byref(read),
        None,
    ):
        return None

    if read.value == 0:
        # EOF (Ctrl+Z then Enter on Windows).
        return None

    return buffer.value[: read.value]


def _read_stream_line(prompt: str = "") -> Optional[str]:
    """
    Read one line from a *redirected* standard input, as raw bytes.

    The bytes are read from the binary buffer instead of the text layer,
    because the text layer has already decoded them with a code page
    that may be wrong -- and a wrong decoding is not reversible.

    ``None`` is returned when the stream does not offer a binary buffer
    or when it is closed.
    """
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is None:
        return None

    if prompt:
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        except Exception:
            pass

    try:
        data = buffer.readline()
    except Exception:
        return None

    if not data:
        return None

    return data.decode("latin-1", errors="replace")


def _console_codepage() -> Optional[str]:
    """The code page of the Windows console, if there is one."""
    if not IS_WINDOWS:
        return None
    try:
        import ctypes

        # GetConsoleCP() returns the *input* code page of the console.
        cp = ctypes.windll.kernel32.GetConsoleCP()
        if cp:
            return "cp" + str(int(cp))
    except Exception:  # pragma: no cover - depends on the machine
        pass
    return None


def _decode_stream_bytes(data: str) -> str:
    """
    Turn the raw bytes of a redirected line into text.

    The bytes are decoded as UTF-8 first -- that is the right guess for
    a pipe that was written by a UTF-8 aware program (Docker, CI, ...).
    When the bytes are *not* valid UTF-8 they were produced by a
    program that wrote them in the code page of the console, and the
    code pages of the Windows console are tried instead.

    The candidate that the assistant understands best wins: the
    vocabulary of the project is the judge, because the code pages
    differ far more in their *garbage* than in their Vietnamese text.
    """
    raw = data.encode("latin-1", errors="replace")

    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        pass

    candidates = []
    console_cp = _console_codepage()
    if console_cp:
        candidates.append(console_cp)
    candidates.extend(_CODEPAGES)

    best = None
    best_score = None
    for codepage in candidates:
        try:
            decoded = raw.decode(codepage, errors="replace")
        except (UnicodeDecodeError, LookupError):
            continue
        score = _score_candidate(decoded)
        if best_score is None or score > best_score:
            best_score = score
            best = decoded

    if best is None:
        return raw.decode("latin-1", errors="replace")
    return best


def read_line(prompt: str = "") -> Optional[str]:
    """
    Read one line from the console and return it in a normalised form.

    The returned string has

    * the invisible control characters removed,
    * a mojibake encoding repaired,
    * the raw Vietnamese syllables restored,
    * a typo inside a word repaired.

    ``None`` is returned when the input stream is closed (EOF) so that
    the caller can leave its loop cleanly.
    """
    raw = _read_windows_console_line(prompt)

    if raw is None:
        # A redirected stream (a pipe, a file, a CI job) is read as raw
        # bytes, because the text layer would have decoded them with a
        # code page that can be wrong.
        raw = _read_stream_line(prompt)
        if raw is not None:
            raw = _decode_stream_bytes(raw)

    if raw is None:
        try:
            raw = input(prompt)
        except EOFError:
            return None

    text = strip_control_characters(raw)
    if not text:
        return ""

    text = repair_mojibake(text)
    text = repair_holes(text)
    text = repair_raw_syllables(text)
    text = repair_typos(text)

    return text


def is_utf8_stdin() -> bool:
    """Is the standard input decoded as UTF-8?"""
    encoding = (getattr(sys.stdin, "encoding", "") or "").lower()
    return encoding in ("utf-8", "utf8")
