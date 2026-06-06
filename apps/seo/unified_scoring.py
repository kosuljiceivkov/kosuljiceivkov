"""Unified SEO scoring engine — agregirana ocena i machine-readable izlaz."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from apps.blog.models import BlogPost
from apps.seo.content_analysis import ContentAnalysisInput, build_content_analysis_input
from apps.seo.internal_linking import analyze_internal_linking
from apps.seo.keyword_analyzer import (
    CheckStatus,
    analyze_keyword_content,
    keyword_in_text,
)
from apps.seo.readability_content import extract_readability_content

ENGINE_VERSION = "1.0"

PLACEMENT_CHECK_IDS = frozenset(
    {
        "keyword_in_seo_title",
        "keyword_in_h1",
        "keyword_in_first_paragraph",
        "keyword_in_url",
        "keyword_in_meta_description",
    }
)

CATEGORY_WEIGHTS: dict[str, int] = {
    "title_optimization": 12,
    "meta_description": 12,
    "keyword_placement": 15,
    "keyword_density": 10,
    "heading_structure": 10,
    "image_alt_text": 8,
    "internal_links": 12,
    "schema_presence": 11,
    "content_length": 10,
}

CATEGORY_LABELS: dict[str, str] = {
    "title_optimization": "Optimizacija naslova",
    "meta_description": "Meta opis",
    "keyword_placement": "Pozicioniranje ključne reči",
    "keyword_density": "Gustina ključne reči",
    "heading_structure": "Struktura naslova",
    "image_alt_text": "Alt tekst slika",
    "internal_links": "Interni linkovi",
    "schema_presence": "Schema.org",
    "content_length": "Dužina sadržaja",
}


def _status_from_score(score: int) -> str:
    if score >= 70:
        return CheckStatus.GOOD.value
    if score >= 40:
        return CheckStatus.OK.value
    return CheckStatus.BAD.value


def _ratio_score(points: int, max_points: int) -> int:
    if max_points <= 0:
        return 0
    return round((points / max_points) * 100)


@dataclass(frozen=True)
class CategoryCheck:
    check_id: str
    label: str
    status: str
    message: str
    score: int
    max_score: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CategoryScore:
    category_id: str
    label: str
    score: int
    weight: int
    weighted_contribution: float
    status: str
    checks: list[CategoryCheck] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.category_id,
            "label": self.label,
            "score": self.score,
            "weight": self.weight,
            "weighted_contribution": self.weighted_contribution,
            "status": self.status,
            "checks": [check.to_dict() for check in self.checks],
            "recommendations": self.recommendations,
        }


@dataclass
class UnifiedSeoScoreResult:
    overall_score: int = 0
    overall_status: str = CheckStatus.NEUTRAL.value
    categories: list[CategoryScore] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    focus_keyword: str = ""
    word_count: int = 0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": ENGINE_VERSION,
            "overall_score": self.overall_score,
            "overall_status": self.overall_status,
            "focus_keyword": self.focus_keyword,
            "word_count": self.word_count,
            "message": self.message,
            "categories": {cat.category_id: cat.to_dict() for cat in self.categories},
            "categories_list": [cat.to_dict() for cat in self.categories],
            "recommendations": self.recommendations,
        }


def _score_title_optimization(analysis_input: ContentAnalysisInput) -> CategoryScore:
    checks: list[CategoryCheck] = []
    recommendations: list[str] = []
    title = analysis_input.seo_title.strip()
    title_len = len(title)

    if 50 <= title_len <= 60:
        length_score = 100
        length_status = CheckStatus.GOOD.value
        length_message = f"SEO naslov ima {title_len} karaktera — idealna dužina (50–60)."
    elif 40 <= title_len <= 70:
        length_score = 70
        length_status = CheckStatus.OK.value
        length_message = f"SEO naslov ima {title_len} karaktera — prihvatljivo (40–70)."
        recommendations.append("Skratite ili produžite SEO naslov na 50–60 karaktera.")
    elif title:
        length_score = 35
        length_status = CheckStatus.BAD.value
        length_message = f"SEO naslov ima {title_len} karaktera — van preporučenog opsega."
        recommendations.append("Optimizujte dužinu SEO naslova na 50–60 karaktera.")
    else:
        length_score = 0
        length_status = CheckStatus.BAD.value
        length_message = "SEO naslov je prazan — koristi se naslov sadržaja."
        recommendations.append("Unesite SEO naslov ili proverite naslov članka.")

    checks.append(
        CategoryCheck(
            check_id="title_length",
            label="Dužina SEO naslova",
            status=length_status,
            message=length_message,
            score=length_score,
        )
    )

    keyword = analysis_input.focus_keyword.strip()
    if keyword:
        in_title = keyword_in_text(keyword, title)
        kw_score = 100 if in_title else 0
        kw_status = CheckStatus.GOOD.value if in_title else CheckStatus.BAD.value
        kw_message = (
            f'Ključna reč „{keyword}” je u SEO naslovu.'
            if in_title
            else f'Dodajte ključnu reč „{keyword}” u SEO naslov.'
        )
        if not in_title:
            recommendations.append(kw_message)
        checks.append(
            CategoryCheck(
                check_id="keyword_in_title",
                label="Ključna reč u naslovu",
                status=kw_status,
                message=kw_message,
                score=kw_score,
            )
        )
        score = round((length_score * 0.55) + (kw_score * 0.45))
    else:
        score = length_score
        checks.append(
            CategoryCheck(
                check_id="keyword_in_title",
                label="Ključna reč u naslovu",
                status=CheckStatus.NEUTRAL.value,
                message="Unesite fokus ključnu reč za proveru naslova.",
                score=50,
            )
        )

    return _build_category(
        "title_optimization",
        score=score,
        checks=checks,
        recommendations=recommendations,
    )


def _score_meta_description(analysis_input: ContentAnalysisInput) -> CategoryScore:
    checks: list[CategoryCheck] = []
    recommendations: list[str] = []
    description = analysis_input.meta_description.strip()
    desc_len = len(description)

    if 120 <= desc_len <= 160:
        length_score = 100
        length_status = CheckStatus.GOOD.value
        length_message = f"Meta opis ima {desc_len} karaktera — idealna dužina."
    elif 80 <= desc_len <= 200:
        length_score = 70
        length_status = CheckStatus.OK.value
        length_message = f"Meta opis ima {desc_len} karaktera — prihvatljivo."
        recommendations.append("Ciljajte meta opis od 120–160 karaktera.")
    elif description:
        length_score = 35
        length_status = CheckStatus.BAD.value
        length_message = f"Meta opis ima {desc_len} karaktera — van preporučenog opsega."
        recommendations.append("Prilagodite meta opis na 120–160 karaktera.")
    else:
        length_score = 0
        length_status = CheckStatus.BAD.value
        length_message = "Meta opis je prazan."
        recommendations.append("Dodajte meta opis (120–160 karaktera).")

    checks.append(
        CategoryCheck(
            check_id="meta_length",
            label="Dužina meta opisa",
            status=length_status,
            message=length_message,
            score=length_score,
        )
    )

    keyword = analysis_input.focus_keyword.strip()
    if keyword:
        in_meta = keyword_in_text(keyword, description)
        kw_score = 100 if in_meta else 0
        kw_status = CheckStatus.GOOD.value if in_meta else CheckStatus.BAD.value
        kw_message = (
            "Ključna reč je u meta opisu."
            if in_meta
            else "Uključite ključnu reč u meta opis."
        )
        if not in_meta:
            recommendations.append(kw_message)
        checks.append(
            CategoryCheck(
                check_id="keyword_in_meta",
                label="Ključna reč u meta opisu",
                status=kw_status,
                message=kw_message,
                score=kw_score,
            )
        )
        score = round((length_score * 0.6) + (kw_score * 0.4))
    else:
        score = length_score

    return _build_category(
        "meta_description",
        score=score,
        checks=checks,
        recommendations=recommendations,
    )


def _score_from_keyword_checks(
    keyword_result,
    *,
    category_id: str,
    check_ids: frozenset[str],
) -> CategoryScore:
    selected = [check for check in keyword_result.checks if check.check_id in check_ids]
    if not selected:
        return _build_category(
            category_id,
            score=50,
            checks=[
                CategoryCheck(
                    check_id="not_applicable",
                    label="N/A",
                    status=CheckStatus.NEUTRAL.value,
                    message="Unesite fokus ključnu reč za ovu kategoriju.",
                    score=50,
                )
            ],
            recommendations=["Definišite fokus ključnu reč."],
        )

    checks = [
        CategoryCheck(
            check_id=check.check_id,
            label=check.label,
            status=check.status.value,
            message=check.message,
            score=_ratio_score(check.points, check.max_points),
        )
        for check in selected
    ]
    total_points = sum(check.points for check in selected)
    max_points = sum(check.max_points for check in selected)
    score = _ratio_score(total_points, max_points)
    recommendations = [check.message for check in selected if check.status == CheckStatus.BAD]

    return _build_category(
        category_id,
        score=score,
        checks=checks,
        recommendations=recommendations,
    )


def _score_heading_structure(content_object, *, visible_only: bool) -> CategoryScore:
    checks: list[CategoryCheck] = []
    recommendations: list[str] = []
    readability_input = extract_readability_content(content_object, visible_only=visible_only)
    headings = readability_input.headings

    has_h1 = any(heading.level == "h1" for heading in headings)
    subheadings = [heading for heading in headings if heading.level in {"h2", "h3", "h4"}]

    if has_h1:
        checks.append(
            CategoryCheck(
                check_id="has_h1",
                label="H1 naslov",
                status=CheckStatus.GOOD.value,
                message="Stranica ima H1 naslov.",
                score=100,
            )
        )
    else:
        checks.append(
            CategoryCheck(
                check_id="has_h1",
                label="H1 naslov",
                status=CheckStatus.BAD.value,
                message="Dodajte jedan H1 naslov u builder.",
                score=0,
            )
        )
        recommendations.append("Dodajte H1 naslov na vrh sadržaja.")

    if subheadings:
        checks.append(
            CategoryCheck(
                check_id="has_subheadings",
                label="Podnaslovi (H2–H4)",
                status=CheckStatus.GOOD.value,
                message=f"Pronađeno {len(subheadings)} podnaslova — dobra struktura.",
                score=100,
            )
        )
    elif readability_input.word_count >= 300:
        checks.append(
            CategoryCheck(
                check_id="has_subheadings",
                label="Podnaslovi (H2–H4)",
                status=CheckStatus.BAD.value,
                message="Duži tekst nema podnaslove — podelite sadržaj H2/H3 naslovima.",
                score=20,
            )
        )
        recommendations.append("Dodajte H2/H3 naslove za bolju strukturu i SEO.")
    else:
        checks.append(
            CategoryCheck(
                check_id="has_subheadings",
                label="Podnaslovi (H2–H4)",
                status=CheckStatus.NEUTRAL.value,
                message="Kratak sadržaj — podnaslovi nisu obavezni.",
                score=70,
            )
        )

    score = round(sum(check.score for check in checks) / len(checks))
    return _build_category(
        "heading_structure",
        score=score,
        checks=checks,
        recommendations=recommendations,
    )


def _score_image_alt_text(content_object, metadata) -> CategoryScore:
    from apps.seo.image_seo import analyze_image_seo

    result = analyze_image_seo(content_object, metadata, visible_only=False)
    if result.message and not result.checks:
        return _build_category(
            "image_alt_text",
            score=0,
            checks=[
                CategoryCheck(
                    check_id="image_seo_unavailable",
                    label="Analiza slika",
                    status=CheckStatus.NEUTRAL.value,
                    message=result.message,
                    score=0,
                )
            ],
            recommendations=[result.message],
        )

    checks = [
        CategoryCheck(
            check_id=check.check_id,
            label=check.label,
            status=check.status.value,
            message=check.message,
            score=_ratio_score(check.points, check.max_points),
        )
        for check in result.checks
    ]
    return _build_category(
        "image_alt_text",
        score=result.score,
        checks=checks,
        recommendations=result.recommendations,
    )


def _score_internal_links(content_object, metadata) -> CategoryScore:
    if not isinstance(content_object, BlogPost):
        return _build_category(
            "internal_links",
            score=70,
            checks=[
                CategoryCheck(
                    check_id="blog_only",
                    label="Interni linkovi",
                    status=CheckStatus.NEUTRAL.value,
                    message="Detaljna analiza internih linkova dostupna je za blog članke.",
                    score=70,
                )
            ],
            recommendations=[],
        )

    linking_result = analyze_internal_linking(content_object, metadata, visible_only=False)
    checks = [
        CategoryCheck(
            check_id=check.check_id,
            label=check.label,
            status=check.status.value,
            message=check.message,
            score=_ratio_score(check.points, check.max_points),
        )
        for check in linking_result.checks
    ]
    return _build_category(
        "internal_links",
        score=linking_result.score,
        checks=checks,
        recommendations=[
            item
            for item in linking_result.recommendations
            if not item.startswith("Odličan rad")
        ][:5],
    )


def _score_schema_presence(content_object, metadata, request=None) -> CategoryScore:
    from apps.seo.schema.engine import preview_schema_bundle

    if content_object is None or not getattr(content_object, "pk", None):
        return _build_category(
            "schema_presence",
            score=0,
            checks=[
                CategoryCheck(
                    check_id="schema_unavailable",
                    label="Schema.org",
                    status=CheckStatus.NEUTRAL.value,
                    message="Sačuvajte sadržaj da biste videli Schema.org validaciju.",
                    score=0,
                )
            ],
            recommendations=["Sačuvajte objavu da generišete JSON-LD."],
        )

    _, _, validation = preview_schema_bundle(
        request,
        content_object,
        metadata=metadata,
        visible_only=False,
    )
    checks = [
        CategoryCheck(
            check_id=f"{check.schema_type}:{check.field}",
            label=f"{check.label} ({check.schema_type})",
            status=check.status.value,
            message=check.message,
            score=100 if check.status == CheckStatus.GOOD else 50 if check.status == CheckStatus.OK else 0,
        )
        for check in validation.checks[:8]
    ]
    if not checks:
        checks.append(
            CategoryCheck(
                check_id="schema_generated",
                label="JSON-LD",
                status=CheckStatus.GOOD.value if validation.schema_types else CheckStatus.BAD.value,
                message=(
                    f"Generisani tipovi: {', '.join(validation.schema_types)}."
                    if validation.schema_types
                    else "Nema generisanog JSON-LD."
                ),
                score=100 if validation.schema_types else 0,
            )
        )

    recommendations = list(validation.warnings[:5]) + [
        check.message
        for check in validation.checks
        if check.status == CheckStatus.BAD
    ][:5]

    return _build_category(
        "schema_presence",
        score=validation.score,
        checks=checks,
        recommendations=recommendations,
    )


def _score_content_length(analysis_input: ContentAnalysisInput, content_object) -> CategoryScore:
    word_count = analysis_input.word_count
    is_blog = isinstance(content_object, BlogPost)
    checks: list[CategoryCheck] = []
    recommendations: list[str] = []

    if is_blog:
        if word_count >= 600:
            score = 100
            status = CheckStatus.GOOD.value
            message = f"Sadržaj ima {word_count} reči — odlična dužina za blog."
        elif word_count >= 300:
            score = 80
            status = CheckStatus.GOOD.value
            message = f"Sadržaj ima {word_count} reči — dobra dužina."
        elif word_count >= 150:
            score = 55
            status = CheckStatus.OK.value
            message = f"Sadržaj ima {word_count} reči — razmislite o proširenju teksta."
            recommendations.append("Proširite članak na najmanje 300 reči za bolji SEO.")
        elif word_count > 0:
            score = 25
            status = CheckStatus.BAD.value
            message = f"Sadržaj ima samo {word_count} reči — prekratko za blog."
            recommendations.append("Dodajte više korisnog sadržaja (min. 300 reči).")
        else:
            score = 0
            status = CheckStatus.BAD.value
            message = "Nema tekstualnog sadržaja u builderu."
            recommendations.append("Dodajte sadržaj u builder.")
    else:
        if word_count >= 150:
            score = 100
            status = CheckStatus.GOOD.value
            message = f"Stranica ima {word_count} reči."
        elif word_count >= 50:
            score = 70
            status = CheckStatus.OK.value
            message = f"Stranica ima {word_count} reči — prihvatljivo za CMS stranicu."
        elif word_count > 0:
            score = 40
            status = CheckStatus.OK.value
            message = f"Stranica ima {word_count} reči."
        else:
            score = 0
            status = CheckStatus.BAD.value
            message = "Nema tekstualnog sadržaja."
            recommendations.append("Dodajte tekstualni sadržaj u builder.")

    checks.append(
        CategoryCheck(
            check_id="word_count",
            label="Broj reči",
            status=status,
            message=message,
            score=score,
        )
    )

    return _build_category(
        "content_length",
        score=score,
        checks=checks,
        recommendations=recommendations,
    )


def _build_category(
    category_id: str,
    *,
    score: int,
    checks: list[CategoryCheck],
    recommendations: list[str],
) -> CategoryScore:
    weight = CATEGORY_WEIGHTS[category_id]
    weighted = round((score * weight) / 100, 1)
    return CategoryScore(
        category_id=category_id,
        label=CATEGORY_LABELS[category_id],
        score=score,
        weight=weight,
        weighted_contribution=weighted,
        status=_status_from_score(score),
        checks=checks,
        recommendations=recommendations[:5],
    )


def _aggregate_recommendations(categories: list[CategoryScore]) -> list[str]:
    seen: set[str] = set()
    aggregated: list[str] = []

    for category in sorted(categories, key=lambda item: item.score):
        for recommendation in category.recommendations:
            if recommendation and recommendation not in seen:
                seen.add(recommendation)
                aggregated.append(recommendation)

    if not aggregated:
        aggregated.append("Odličan rad — SEO je dobro optimizovan.")

    return aggregated[:15]


def analyze_unified_seo(
    content_object,
    metadata=None,
    *,
    request=None,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> UnifiedSeoScoreResult:
    if content_object is None:
        return UnifiedSeoScoreResult(message="Nema sadržaja za analizu.")

    analysis_input = build_content_analysis_input(
        content_object,
        metadata,
        overrides=overrides,
        visible_only=visible_only,
    )
    keyword_result = analyze_keyword_content(analysis_input)

    categories = [
        _score_title_optimization(analysis_input),
        _score_meta_description(analysis_input),
        _score_from_keyword_checks(
            keyword_result,
            category_id="keyword_placement",
            check_ids=PLACEMENT_CHECK_IDS,
        ),
        _score_from_keyword_checks(
            keyword_result,
            category_id="keyword_density",
            check_ids=frozenset({"keyword_density", "keyword_distribution"}),
        ),
        _score_heading_structure(content_object, visible_only=visible_only),
        _score_image_alt_text(content_object, metadata),
        _score_internal_links(content_object, metadata),
        _score_schema_presence(content_object, metadata, request=request),
        _score_content_length(analysis_input, content_object),
    ]

    overall_score = round(sum(category.weighted_contribution for category in categories))
    overall_score = max(0, min(100, overall_score))

    return UnifiedSeoScoreResult(
        overall_score=overall_score,
        overall_status=_status_from_score(overall_score),
        categories=categories,
        recommendations=_aggregate_recommendations(categories),
        focus_keyword=analysis_input.focus_keyword,
        word_count=analysis_input.word_count,
    )


def compute_unified_seo_score(
    content_object,
    metadata=None,
    *,
    request=None,
    visible_only: bool = False,
) -> int:
    """Kratki helper — vraća samo ukupnu ocenu 0–100."""
    result = analyze_unified_seo(
        content_object,
        metadata,
        request=request,
        visible_only=visible_only,
    )
    return result.overall_score
