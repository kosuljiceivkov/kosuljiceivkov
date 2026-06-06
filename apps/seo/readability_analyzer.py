"""Yoast-style analiza čitljivosti."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum

from apps.seo.readability_content import ReadabilityContentInput, build_readability_content_input

LONG_SENTENCE_WORDS = 20
IDEAL_SENTENCE_WORDS = (15, 20)
MAX_PARAGRAPH_WORDS = 150
MAX_PARAGRAPH_HARD = 200
HEADING_WORD_GAP = 300
MIN_WORDS_FOR_HEADING_CHECK = 300
MIN_WORDS_FOR_TRANSITION_CHECK = 150

TRANSITION_WORDS = (
    "međutim",
    "medjutim",
    "dakle",
    "takođe",
    "takodje",
    "takodje",
    "zato",
    "jer",
    "ipak",
    "na primer",
    "npr",
    "ukratko",
    "pre svega",
    "pored toga",
    "osim toga",
    "stoga",
    "zatim",
    "nakon toga",
    "prvo",
    "drugo",
    "treće",
    "trece",
    "na kraju",
    "zaključno",
    "zakljucno",
    "naravno",
    "posebno",
    "zbog toga",
    "uostalom",
    "štaviše",
    "staviše",
    "s druge strane",
    "s jedne strane",
    "ukoliko",
    "mada",
    "iako",
    "tako",
    "zato što",
    "zato sto",
)

PASSIVE_PATTERNS = (
    re.compile(r"\b(je|su|smo|ste|sam|si)\s+(bio|bila|bilo|bili|bile)\b", re.I),
    re.compile(r"\b(biće|bice)\s+\S+", re.I),
    re.compile(r"\b(je|su)\s+\S+(an|en|na|no|ni|ne|nut|nuta|eno)\b", re.I),
    re.compile(r"\b\S+\s+se\s+(može|moze|mora|treba|koristi|koriste|radi|rade|vidi|vidi)\b", re.I),
)


class CheckStatus(StrEnum):
    GOOD = "good"
    OK = "ok"
    BAD = "bad"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class ReadabilityCheck:
    check_id: str
    label: str
    status: CheckStatus
    message: str
    points: int
    max_points: int
    is_warning: bool = False


@dataclass
class ReadabilityAnalysisResult:
    score: int
    difficulty_label: str
    checks: list[ReadabilityCheck] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "difficulty_label": self.difficulty_label,
            "checks": [
                {
                    **asdict(check),
                    "status": check.status.value,
                }
                for check in self.checks
            ],
            "recommendations": self.recommendations,
            "warnings": self.warnings,
        }


def _paragraph_word_counts(paragraphs: list[str]) -> list[int]:
    return [len(paragraph.split()) for paragraph in paragraphs if paragraph.strip()]


def _sentence_word_counts(sentences: list[str]) -> list[int]:
    return [len(sentence.split()) for sentence in sentences if sentence.strip()]


def _contains_transition_word(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in TRANSITION_WORDS)


def _is_passive_sentence(sentence: str) -> bool:
    return any(pattern.search(sentence) for pattern in PASSIVE_PATTERNS)


def _estimate_difficulty(content_input: ReadabilityContentInput) -> tuple[int, str]:
    if content_input.word_count == 0:
        return 0, "N/A"

    sentence_counts = _sentence_word_counts(content_input.sentences)
    if not sentence_counts:
        return 0, "N/A"

    avg_sentence = sum(sentence_counts) / len(sentence_counts)
    words = content_input.content.split()
    avg_word_len = sum(len(word.strip(".,!?;:")) for word in words) / len(words)

    score = 100
    score -= max(0, (avg_sentence - 18) * 2.5)
    score -= max(0, (avg_word_len - 6.5) * 6)
    score = max(0, min(100, int(score)))

    if score >= 70:
        label = "Lako"
    elif score >= 45:
        label = "Srednje"
    else:
        label = "Teško"

    return score, label


def _heading_gap_issue(content_input: ReadabilityContentInput) -> tuple[bool, str]:
    if content_input.word_count < MIN_WORDS_FOR_HEADING_CHECK:
        return False, "Tekst je dovoljno kratak — podnaslovi nisu obavezni."

    subheadings = [
        heading for heading in content_input.headings if heading.level in {"h2", "h3", "h4"}
    ]
    if not subheadings:
        return True, "Dodajte podnaslove (H2/H3) za bolju strukturu i čitljivost."

    words = content_input.content.split()
    if len(words) <= HEADING_WORD_GAP:
        return False, "Podnaslovi su prisutni."

    chunk_size = HEADING_WORD_GAP
    for index in range(0, len(words), chunk_size):
        chunk = " ".join(words[index : index + chunk_size])
        if not any(heading.text.lower() in chunk.lower() for heading in subheadings):
            if index + chunk_size < len(words):
                return True, f"Svakih ~{HEADING_WORD_GAP} reči treba podnaslov — proverite raspodelu."

    return False, "Podnaslovi su ravnomerno raspoređeni."


def _make_check(
    check_id: str,
    label: str,
    *,
    passed: bool,
    partial: bool = False,
    good_message: str,
    ok_message: str,
    bad_message: str,
    max_points: int,
    is_warning: bool = False,
) -> ReadabilityCheck:
    if passed:
        status = CheckStatus.GOOD
        message = good_message
        points = max_points
    elif partial:
        status = CheckStatus.OK
        message = ok_message
        points = max(max_points // 2, 1)
        is_warning = is_warning or True
    else:
        status = CheckStatus.BAD
        message = bad_message
        points = 0
        is_warning = True

    return ReadabilityCheck(
        check_id=check_id,
        label=label,
        status=status,
        message=message,
        points=points,
        max_points=max_points,
        is_warning=is_warning,
    )


def analyze_readability(content_input: ReadabilityContentInput) -> ReadabilityAnalysisResult:
    result = ReadabilityAnalysisResult(score=0, difficulty_label="N/A")

    if content_input.word_count == 0:
        result.checks = [
            ReadabilityCheck(
                check_id="no_content",
                label="Sadržaj",
                status=CheckStatus.NEUTRAL,
                message="Nema dovoljno teksta za analizu čitljivosti.",
                points=0,
                max_points=0,
            )
        ]
        result.recommendations = ["Dodajte tekstualni sadržaj u builder ili uvod."]
        return result

    checks: list[ReadabilityCheck] = []
    sentence_counts = _sentence_word_counts(content_input.sentences)
    avg_sentence = sum(sentence_counts) / len(sentence_counts) if sentence_counts else 0
    long_sentence_ratio = (
        sum(1 for count in sentence_counts if count > LONG_SENTENCE_WORDS) / len(sentence_counts)
        if sentence_counts
        else 0
    )

    if IDEAL_SENTENCE_WORDS[0] <= avg_sentence <= IDEAL_SENTENCE_WORDS[1] and long_sentence_ratio <= 0.25:
        checks.append(
            _make_check(
                "sentence_length",
                "Dužina rečenica",
                passed=True,
                good_message=(
                    f"Prosečna dužina je {avg_sentence:.0f} reči — odlično "
                    f"(preporuka: {IDEAL_SENTENCE_WORDS[0]}–{IDEAL_SENTENCE_WORDS[1]})."
                ),
                ok_message="",
                bad_message="",
                max_points=18,
            )
        )
    elif avg_sentence <= 25 and long_sentence_ratio <= 0.4:
        checks.append(
            ReadabilityCheck(
                check_id="sentence_length",
                label="Dužina rečenica",
                status=CheckStatus.OK,
                message=(
                    f"Prosečno {avg_sentence:.0f} reči po rečenici. "
                    f"{int(long_sentence_ratio * 100)}% rečenica je predugačko."
                ),
                points=10,
                max_points=18,
                is_warning=True,
            )
        )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="sentence_length",
                label="Dužina rečenica",
                status=CheckStatus.BAD,
                message=(
                    f"Prosečno {avg_sentence:.0f} reči — skratite rečenice "
                    f"(idealno {IDEAL_SENTENCE_WORDS[0]}–{IDEAL_SENTENCE_WORDS[1]})."
                ),
                points=0,
                max_points=18,
                is_warning=True,
            )
        )

    paragraph_counts = _paragraph_word_counts(content_input.paragraphs)
    avg_paragraph = sum(paragraph_counts) / len(paragraph_counts) if paragraph_counts else 0
    max_paragraph = max(paragraph_counts) if paragraph_counts else 0

    if avg_paragraph <= MAX_PARAGRAPH_WORDS and max_paragraph <= MAX_PARAGRAPH_HARD:
        checks.append(
            _make_check(
                "paragraph_length",
                "Dužina pasusa",
                passed=True,
                good_message=(
                    f"Prosečan pasus ima {avg_paragraph:.0f} reči "
                    f"(preporuka: do {MAX_PARAGRAPH_WORDS})."
                ),
                ok_message="",
                bad_message="",
                max_points=16,
            )
        )
    elif max_paragraph <= MAX_PARAGRAPH_HARD + 80:
        checks.append(
            ReadabilityCheck(
                check_id="paragraph_length",
                label="Dužina pasusa",
                status=CheckStatus.OK,
                message=f"Najduži pasus ima {max_paragraph} reči — razbijte ga na kraće delove.",
                points=8,
                max_points=16,
                is_warning=True,
            )
        )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="paragraph_length",
                label="Dužina pasusa",
                status=CheckStatus.BAD,
                message=f"Pasus od {max_paragraph} reči je predugačak — dodajte prazne redove.",
                points=0,
                max_points=16,
                is_warning=True,
            )
        )

    passive_sentences = sum(1 for sentence in content_input.sentences if _is_passive_sentence(sentence))
    passive_ratio = passive_sentences / len(content_input.sentences) if content_input.sentences else 0

    if passive_ratio <= 0.10:
        checks.append(
            _make_check(
                "passive_voice",
                "Pasiv",
                passed=True,
                good_message=f"Pasiv u {int(passive_ratio * 100)}% rečenica — odlično (ispod 10%).",
                ok_message="",
                bad_message="",
                max_points=14,
            )
        )
    elif passive_ratio <= 0.20:
        checks.append(
            ReadabilityCheck(
                check_id="passive_voice",
                label="Pasiv",
                status=CheckStatus.OK,
                message=f"Pasiv u {int(passive_ratio * 100)}% rečenica — smanjite na ispod 10%.",
                points=7,
                max_points=14,
                is_warning=True,
            )
        )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="passive_voice",
                label="Pasiv",
                status=CheckStatus.BAD,
                message=f"Previše pasiva ({int(passive_ratio * 100)}%) — koristite aktivne konstrukcije.",
                points=0,
                max_points=14,
                is_warning=True,
            )
        )

    if content_input.word_count >= MIN_WORDS_FOR_TRANSITION_CHECK:
        transition_paragraphs = sum(
            1 for paragraph in content_input.paragraphs if _contains_transition_word(paragraph)
        )
        transition_ratio = (
            transition_paragraphs / len(content_input.paragraphs) if content_input.paragraphs else 0
        )

        if transition_ratio >= 0.30:
            checks.append(
                _make_check(
                    "transition_words",
                    "Prelazne reči",
                    passed=True,
                    good_message=(
                        f"Prelazne reči u {int(transition_ratio * 100)}% pasusa — "
                        "dobar tok teksta."
                    ),
                    ok_message="",
                    bad_message="",
                    max_points=14,
                )
            )
        elif transition_ratio >= 0.15:
            checks.append(
                ReadabilityCheck(
                    check_id="transition_words",
                    label="Prelazne reči",
                    status=CheckStatus.OK,
                    message="Dodajte više prelaznih reči (npr. „međutim”, „takođe”, „zato”).",
                    points=7,
                    max_points=14,
                    is_warning=True,
                )
            )
        else:
            checks.append(
                ReadabilityCheck(
                    check_id="transition_words",
                    label="Prelazne reči",
                    status=CheckStatus.BAD,
                    message="Tekstu nedostaju prelazne reči — uvođenja pasusa su oštra.",
                    points=0,
                    max_points=14,
                    is_warning=True,
                )
            )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="transition_words",
                label="Prelazne reči",
                status=CheckStatus.NEUTRAL,
                message="Tekst je prekratak za proveru prelaznih reči.",
                points=14,
                max_points=14,
            )
        )

    has_heading_issue, heading_message = _heading_gap_issue(content_input)
    if not has_heading_issue:
        checks.append(
            _make_check(
                "heading_distribution",
                "Raspodela naslova",
                passed=True,
                good_message=heading_message,
                ok_message="",
                bad_message="",
                max_points=18,
            )
        )
    elif content_input.word_count < MIN_WORDS_FOR_HEADING_CHECK:
        checks.append(
            ReadabilityCheck(
                check_id="heading_distribution",
                label="Raspodela naslova",
                status=CheckStatus.OK,
                message=heading_message,
                points=12,
                max_points=18,
            )
        )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="heading_distribution",
                label="Raspodela naslova",
                status=CheckStatus.BAD,
                message=heading_message,
                points=0,
                max_points=18,
                is_warning=True,
            )
        )

    difficulty_score, difficulty_label = _estimate_difficulty(content_input)
    if difficulty_score >= 70:
        checks.append(
            _make_check(
                "reading_difficulty",
                "Težina čitanja",
                passed=True,
                good_message=f"Nivo: {difficulty_label} — tekst je lako čitljiv.",
                ok_message="",
                bad_message="",
                max_points=20,
            )
        )
    elif difficulty_score >= 45:
        checks.append(
            ReadabilityCheck(
                check_id="reading_difficulty",
                label="Težina čitanja",
                status=CheckStatus.OK,
                message=f"Nivo: {difficulty_label} — pojednostavite rečenice gde je moguće.",
                points=10,
                max_points=20,
                is_warning=True,
            )
        )
    else:
        checks.append(
            ReadabilityCheck(
                check_id="reading_difficulty",
                label="Težina čitanja",
                status=CheckStatus.BAD,
                message=f"Nivo: {difficulty_label} — skratite rečenice i koristite jednostavnije reči.",
                points=0,
                max_points=20,
                is_warning=True,
            )
        )

    total_points = sum(check.points for check in checks)
    max_total = sum(check.max_points for check in checks)
    score = round((total_points / max_total) * 100) if max_total else 0

    warnings = [check.message for check in checks if check.is_warning and check.status == CheckStatus.BAD]
    recommendations = [
        check.message
        for check in checks
        if check.status in {CheckStatus.BAD, CheckStatus.OK}
    ]
    if score >= 70 and not warnings:
        recommendations = ["Odlična čitljivost — nastavite sa jasnim pasusima i podnaslovima."]

    result.score = score
    result.difficulty_label = difficulty_label
    result.checks = checks
    result.warnings = warnings
    result.recommendations = recommendations
    return result


def analyze_readability_for_object(
    content_object,
    *,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> ReadabilityAnalysisResult:
    content_input = build_readability_content_input(
        content_object,
        overrides=overrides,
        visible_only=visible_only,
    )
    return analyze_readability(content_input)
