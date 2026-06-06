"""Yoast-style analiza fokus ključne reči."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum

from apps.seo.content_analysis import ContentAnalysisInput, build_content_analysis_input
from apps.seo.content_text import normalize_whitespace

WORD_BOUNDARY = r"(?<![\w\u0100-\u024F])"
WORD_BOUNDARY_END = r"(?![\w\u0100-\u024F])"


class CheckStatus(StrEnum):
    GOOD = "good"
    OK = "ok"
    BAD = "bad"
    NEUTRAL = "neutral"


STATUS_LABELS = {
    CheckStatus.GOOD: "Odlično",
    CheckStatus.OK: "Može bolje",
    CheckStatus.BAD: "Potrebno poboljšanje",
    CheckStatus.NEUTRAL: "N/A",
}


@dataclass(frozen=True)
class KeywordCheck:
    check_id: str
    label: str
    status: CheckStatus
    message: str
    points: int
    max_points: int

    @property
    def score_ratio(self) -> float:
        if self.max_points <= 0:
            return 0.0
        return self.points / self.max_points


@dataclass
class KeywordAnalysisResult:
    focus_keyword: str
    score: int
    checks: list[KeywordCheck] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "focus_keyword": self.focus_keyword,
            "score": self.score,
            "checks": [
                {
                    **asdict(check),
                    "status": check.status.value,
                    "status_label": STATUS_LABELS[check.status],
                }
                for check in self.checks
            ],
            "recommendations": self.recommendations,
        }


def _normalize_keyword(keyword: str) -> str:
    return normalize_whitespace(keyword.lower())


def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(_normalize_keyword(keyword))
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"{WORD_BOUNDARY}{escaped}{WORD_BOUNDARY_END}", re.IGNORECASE)


def keyword_in_text(keyword: str, text: str) -> bool:
    if not keyword or not text:
        return False
    return bool(_keyword_pattern(keyword).search(normalize_whitespace(text)))


def count_keyword_occurrences(keyword: str, text: str) -> int:
    if not keyword or not text:
        return 0
    return len(_keyword_pattern(keyword).findall(normalize_whitespace(text)))


def keyword_density_percent(keyword: str, text: str) -> float:
    if not keyword or not text:
        return 0.0

    words = normalize_whitespace(text).split()
    if not words:
        return 0.0

    keyword_word_count = len(_normalize_keyword(keyword).split())
    occurrences = count_keyword_occurrences(keyword, text)
    return (occurrences * keyword_word_count / len(words)) * 100


def keyword_in_slug(keyword: str, slug: str) -> bool:
    if not keyword or not slug:
        return False

    slug_text = slug.lower().replace("-", " ").replace("_", " ")
    keyword_words = _normalize_keyword(keyword).split()
    return all(word in slug_text for word in keyword_words)


def _distribution_thirds(content: str, keyword: str) -> tuple[bool, bool, bool]:
    words = normalize_whitespace(content).split()
    if not words:
        return False, False, False

    third = max(len(words) // 3, 1)
    parts = [
        " ".join(words[0:third]),
        " ".join(words[third : third * 2]),
        " ".join(words[third * 2 :]),
    ]
    return tuple(keyword_in_text(keyword, part) for part in parts)


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
) -> KeywordCheck:
    if passed:
        status = CheckStatus.GOOD
        message = good_message
        points = max_points
    elif partial:
        status = CheckStatus.OK
        message = ok_message
        points = max(max_points // 2, 1)
    else:
        status = CheckStatus.BAD
        message = bad_message
        points = 0

    return KeywordCheck(
        check_id=check_id,
        label=label,
        status=status,
        message=message,
        points=points,
        max_points=max_points,
    )


def analyze_keyword_content(analysis_input: ContentAnalysisInput) -> KeywordAnalysisResult:
    keyword = analysis_input.focus_keyword.strip()
    result = KeywordAnalysisResult(focus_keyword=keyword, score=0)

    if not keyword:
        result.checks = [
            KeywordCheck(
                check_id="focus_keyword_missing",
                label="Fokus ključna reč",
                status=CheckStatus.NEUTRAL,
                message="Unesite fokus ključnu reč da biste pokrenuli analizu.",
                points=0,
                max_points=0,
            )
        ]
        result.recommendations = [
            "Definišite jednu glavnu ključnu reč za ovaj članak.",
        ]
        return result

    checks: list[KeywordCheck] = []

    checks.append(
        _make_check(
            "keyword_in_seo_title",
            "Ključna reč u SEO naslovu",
            passed=keyword_in_text(keyword, analysis_input.seo_title),
            good_message=f'Ključna reč „{keyword}” je u SEO naslovu.',
            ok_message="",
            bad_message=f'Dodajte „{keyword}” u SEO naslov (ili koristite u naslovu članka).',
            max_points=12,
        )
    )

    checks.append(
        _make_check(
            "keyword_in_h1",
            "Ključna reč u H1",
            passed=keyword_in_text(keyword, analysis_input.h1),
            good_message=f'Ključna reč je u H1: „{analysis_input.h1[:80]}”.',
            ok_message="",
            bad_message="Uključite ključnu reč u prvi H1 naslov u sadržaju.",
            max_points=12,
        )
    )

    checks.append(
        _make_check(
            "keyword_in_first_paragraph",
            "Ključna reč u prvom pasusu",
            passed=keyword_in_text(keyword, analysis_input.first_paragraph),
            good_message="Ključna reč se pojavljuje u uvodu / prvom pasusu.",
            ok_message="",
            bad_message="Pomenite ključnu reč u prvom pasusu ili uvodu članka.",
            max_points=12,
        )
    )

    in_url = keyword_in_slug(keyword, analysis_input.url_slug)
    checks.append(
        _make_check(
            "keyword_in_url",
            "Ključna reč u URL-u",
            passed=in_url,
            good_message=f'Slug „{analysis_input.url_slug}” sadrži ključnu reč.',
            ok_message="",
            bad_message="Prilagodite slug URL-a da uključi glavnu ključnu reč.",
            max_points=10,
        )
    )

    checks.append(
        _make_check(
            "keyword_in_meta_description",
            "Ključna reč u meta opisu",
            passed=keyword_in_text(keyword, analysis_input.meta_description),
            good_message="Ključna reč je prisutna u meta opisu.",
            ok_message="",
            bad_message="Uključite ključnu reč u meta opis (150–160 karaktera).",
            max_points=12,
        )
    )

    density = keyword_density_percent(keyword, analysis_input.content)
    if 0.5 <= density <= 2.5:
        density_check = _make_check(
            "keyword_density",
            "Gustina ključne reči",
            passed=True,
            good_message=f"Gustina je {density:.1f}% — u preporučenom opsegu (0,5–2,5%).",
            ok_message="",
            bad_message="",
            max_points=15,
        )
    elif 0.2 <= density < 0.5 or 2.5 < density <= 3.5:
        density_check = KeywordCheck(
            check_id="keyword_density",
            label="Gustina ključne reči",
            status=CheckStatus.OK,
            message=f"Gustina je {density:.1f}%. Ciljajte 0,5–2,5%.",
            points=8,
            max_points=15,
        )
    elif density == 0:
        density_check = _make_check(
            "keyword_density",
            "Gustina ključne reči",
            passed=False,
            good_message="",
            ok_message="",
            bad_message="Ključna reč se ne pojavljuje u tekstu sadržaja.",
            max_points=15,
        )
    else:
        density_check = KeywordCheck(
            check_id="keyword_density",
            label="Gustina ključne reči",
            status=CheckStatus.BAD,
            message=f"Gustina je {density:.1f}% — preniska ili previsoka. Ciljajte 0,5–2,5%.",
            points=3,
            max_points=15,
        )
    checks.append(density_check)

    first_third, second_third, third_third = _distribution_thirds(analysis_input.content, keyword)
    distribution_hits = sum((first_third, second_third, third_third))
    checks.append(
        KeywordCheck(
            check_id="keyword_distribution",
            label="Raspodela ključne reči",
            status=(
                CheckStatus.GOOD
                if distribution_hits == 3
                else CheckStatus.OK
                if distribution_hits == 2
                else CheckStatus.BAD
            ),
            message=(
                "Ključna reč je ravnomerno raspoređena kroz tekst (3/3 dela)."
                if distribution_hits == 3
                else f"Ključna reč je u {distribution_hits}/3 dela teksta — pokušajte ravnomerniju raspodelu."
                if distribution_hits > 0
                else "Ključna reč nije prisutna u tekstu sadržaja."
            ),
            points=17 if distribution_hits == 3 else 10 if distribution_hits == 2 else 0,
            max_points=17,
        )
    )

    alt_matches = [
        alt for alt in analysis_input.image_alt_texts if keyword_in_text(keyword, alt)
    ]
    has_alts = bool(analysis_input.image_alt_texts)
    checks.append(
        KeywordCheck(
            check_id="keyword_in_image_alt",
            label="Ključna reč u alt tekstu slike",
            status=(
                CheckStatus.GOOD
                if alt_matches
                else CheckStatus.OK
                if not has_alts
                else CheckStatus.BAD
            ),
            message=(
                f"Ključna reč je u alt tekstu ({len(alt_matches)} slika)."
                if alt_matches
                else "Nema slika sa alt tekstom — dodajte slike u builder."
                if not has_alts
                else "Dodajte ključnu reč u alt tekst barem jedne slike."
            ),
            points=10 if alt_matches else 4 if not has_alts else 0,
            max_points=10,
        )
    )

    total_points = sum(check.points for check in checks)
    max_total = sum(check.max_points for check in checks)
    score = round((total_points / max_total) * 100) if max_total else 0

    recommendations = _build_recommendations(checks, keyword, density)

    result.checks = checks
    result.score = score
    result.recommendations = recommendations
    return result


def _build_recommendations(
    checks: list[KeywordCheck],
    keyword: str,
    density: float,
) -> list[str]:
    recommendations: list[str] = []

    for check in checks:
        if check.status == CheckStatus.BAD:
            recommendations.append(check.message)

    if density > 2.5:
        recommendations.append(
            f'Ključna reč „{keyword}” se previše ponavlja — smanjite gustinu ispod 2,5%.'
        )

    if not recommendations:
        recommendations.append("Odličan rad — ključna reč je dobro optimizovana.")

    return recommendations


def analyze_content_object(
    content_object,
    metadata=None,
    *,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> KeywordAnalysisResult:
    analysis_input = build_content_analysis_input(
        content_object,
        metadata,
        overrides=overrides,
        visible_only=visible_only,
    )
    return analyze_keyword_content(analysis_input)
