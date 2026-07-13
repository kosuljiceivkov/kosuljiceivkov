"""AI/LLM readiness analiza — koliko je sadržaj razumljiv AI pretragama i asistentima."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from apps.seo.content_analysis import build_content_analysis_input
from apps.seo.keyword_analyzer import CheckStatus, STATUS_LABELS
from apps.seo.readability_content import build_readability_content_input
from apps.seo.schema.faq import extract_faq_items
from apps.seo.services import get_seo_metadata, resolve_schema_type

FIRST_PARAGRAPH_MIN_WORDS = 25
FIRST_PARAGRAPH_MAX_WORDS = 120
CONTENT_MIN_WORDS = 300
H1_MAX_LENGTH = 90


@dataclass(frozen=True)
class AiReadinessCheck:
    check_id: str
    label: str
    status: CheckStatus
    message: str
    points: int
    max_points: int


@dataclass
class AiReadinessResult:
    score: int = 0
    checks: list[AiReadinessCheck] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "message": self.message,
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


def _check_h1(h1: str) -> AiReadinessCheck:
    value = (h1 or "").strip()
    if not value:
        return AiReadinessCheck(
            check_id="ai_h1",
            label="Jasan H1 naslov",
            status=CheckStatus.BAD,
            message="Nema H1 naslova — AI sistemi ne mogu da odrede temu stranice.",
            points=0,
            max_points=20,
        )
    if len(value) > H1_MAX_LENGTH:
        return AiReadinessCheck(
            check_id="ai_h1",
            label="Jasan H1 naslov",
            status=CheckStatus.OK,
            message=f"H1 je dugačak ({len(value)} karaktera) — kraći naslov je jasniji.",
            points=12,
            max_points=20,
        )
    return AiReadinessCheck(
        check_id="ai_h1",
        label="Jasan H1 naslov",
        status=CheckStatus.GOOD,
        message="H1 jasno opisuje temu stranice.",
        points=20,
        max_points=20,
    )


def _check_first_paragraph(first_paragraph: str) -> AiReadinessCheck:
    words = len((first_paragraph or "").split())
    if words == 0:
        return AiReadinessCheck(
            check_id="ai_first_paragraph",
            label="Direktan odgovor na početku",
            status=CheckStatus.BAD,
            message="Nema uvodnog pasusa — počnite direktnim odgovorom na glavno pitanje.",
            points=0,
            max_points=20,
        )
    if words < FIRST_PARAGRAPH_MIN_WORDS:
        return AiReadinessCheck(
            check_id="ai_first_paragraph",
            label="Direktan odgovor na početku",
            status=CheckStatus.OK,
            message=f"Uvodni pasus je kratak ({words} reči) — proširite ga u samostalan odgovor.",
            points=10,
            max_points=20,
        )
    if words > FIRST_PARAGRAPH_MAX_WORDS:
        return AiReadinessCheck(
            check_id="ai_first_paragraph",
            label="Direktan odgovor na početku",
            status=CheckStatus.OK,
            message=f"Uvodni pasus je dugačak ({words} reči) — sažmite ključni odgovor.",
            points=12,
            max_points=20,
        )
    return AiReadinessCheck(
        check_id="ai_first_paragraph",
        label="Direktan odgovor na početku",
        status=CheckStatus.GOOD,
        message=f"Uvodni pasus ({words} reči) daje samostalan odgovor.",
        points=20,
        max_points=20,
    )


def _check_headings_structure(headings) -> AiReadinessCheck:
    subheadings = [entry for entry in headings if entry.level != "h1"]
    if len(subheadings) >= 2:
        return AiReadinessCheck(
            check_id="ai_headings",
            label="Struktura podnaslova",
            status=CheckStatus.GOOD,
            message=f"{len(subheadings)} podnaslova — sadržaj je lako parsirati po sekcijama.",
            points=15,
            max_points=15,
        )
    if len(subheadings) == 1:
        return AiReadinessCheck(
            check_id="ai_headings",
            label="Struktura podnaslova",
            status=CheckStatus.OK,
            message="Samo jedan podnaslov — podelite sadržaj u više jasnih sekcija.",
            points=8,
            max_points=15,
        )
    return AiReadinessCheck(
        check_id="ai_headings",
        label="Struktura podnaslova",
        status=CheckStatus.BAD,
        message="Nema podnaslova (H2/H3) — AI teže izdvaja odgovore iz neprekinutog teksta.",
        points=0,
        max_points=15,
    )


def _check_faq(content_object) -> AiReadinessCheck:
    faq_items = extract_faq_items(content_object, visible_only=False)
    if len(faq_items) >= 2:
        return AiReadinessCheck(
            check_id="ai_faq",
            label="FAQ sadržaj",
            status=CheckStatus.GOOD,
            message=f"{len(faq_items)} FAQ parova — idealno za AI odgovore i rich results.",
            points=15,
            max_points=15,
        )
    if len(faq_items) == 1:
        return AiReadinessCheck(
            check_id="ai_faq",
            label="FAQ sadržaj",
            status=CheckStatus.OK,
            message="Jedan FAQ par — dodajte još pitanja koja korisnici stvarno postavljaju.",
            points=8,
            max_points=15,
        )
    return AiReadinessCheck(
        check_id="ai_faq",
        label="FAQ sadržaj",
        status=CheckStatus.OK,
        message="Nema FAQ bloka — pitanja i odgovori pomažu AI sistemima da citiraju sadržaj.",
        points=5,
        max_points=15,
    )


def _check_schema(content_object, metadata) -> AiReadinessCheck:
    schema_type = resolve_schema_type(content_object, metadata)
    if schema_type:
        return AiReadinessCheck(
            check_id="ai_schema",
            label="Strukturirani podaci",
            status=CheckStatus.GOOD,
            message=f"JSON-LD šema je aktivna ({schema_type}).",
            points=15,
            max_points=15,
        )
    return AiReadinessCheck(
        check_id="ai_schema",
        label="Strukturirani podaci",
        status=CheckStatus.BAD,
        message="Nema JSON-LD šeme — strukturirani podaci su glavni signal za AI pretrage.",
        points=0,
        max_points=15,
    )


def _check_content_depth(word_count: int) -> AiReadinessCheck:
    if word_count >= CONTENT_MIN_WORDS:
        return AiReadinessCheck(
            check_id="ai_content_depth",
            label="Dubina sadržaja",
            status=CheckStatus.GOOD,
            message=f"Sadržaj od {word_count} reči daje dovoljno konteksta.",
            points=15,
            max_points=15,
        )
    if word_count >= CONTENT_MIN_WORDS // 2:
        return AiReadinessCheck(
            check_id="ai_content_depth",
            label="Dubina sadržaja",
            status=CheckStatus.OK,
            message=f"Sadržaj od {word_count} reči je tanak — ciljajte {CONTENT_MIN_WORDS}+ reči.",
            points=8,
            max_points=15,
        )
    return AiReadinessCheck(
        check_id="ai_content_depth",
        label="Dubina sadržaja",
        status=CheckStatus.BAD,
        message=f"Samo {word_count} reči — prekratko za pouzdane AI odgovore.",
        points=0,
        max_points=15,
    )


def analyze_ai_readiness(
    content_object,
    metadata=None,
    *,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> AiReadinessResult:
    if content_object is None or not getattr(content_object, "pk", None):
        return AiReadinessResult(
            message="Sačuvajte objavu da biste videli AI readiness analizu.",
        )

    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    analysis_input = build_content_analysis_input(
        content_object,
        metadata,
        overrides=overrides,
        visible_only=visible_only,
    )
    readability_input = build_readability_content_input(
        content_object,
        overrides=overrides,
        visible_only=visible_only,
    )

    checks = [
        _check_h1(analysis_input.h1),
        _check_first_paragraph(analysis_input.first_paragraph),
        _check_headings_structure(readability_input.headings),
        _check_faq(content_object),
        _check_schema(content_object, metadata),
        _check_content_depth(analysis_input.word_count),
    ]

    total_points = sum(check.points for check in checks)
    max_points = sum(check.max_points for check in checks)
    score = round((total_points / max_points) * 100) if max_points else 0

    recommendations: list[str] = []
    for check in checks:
        if check.points < check.max_points:
            recommendations.append(check.message)
    if not recommendations:
        recommendations.append("Odlično — sadržaj je spreman za AI pretrage i asistente.")

    return AiReadinessResult(
        score=score,
        checks=checks,
        recommendations=recommendations[:8],
    )
