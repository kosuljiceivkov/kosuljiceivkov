"""Validacija JSON-LD prema Google Rich Results preporukama."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from apps.seo.schema.faq import extract_faq_items


class CheckStatus(StrEnum):
    GOOD = "good"
    OK = "ok"
    BAD = "bad"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class SchemaValidationCheck:
    schema_type: str
    field: str
    label: str
    status: CheckStatus
    message: str


@dataclass
class SchemaValidationResult:
    score: int = 0
    checks: list[SchemaValidationCheck] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    schema_types: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "checks": [
                {
                    "schema_type": check.schema_type,
                    "field": check.field,
                    "label": check.label,
                    "status": check.status.value,
                    "message": check.message,
                }
                for check in self.checks
            ],
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "schema_types": self.schema_types,
        }


def _add_check(
    checks: list[SchemaValidationCheck],
    *,
    schema_type: str,
    field: str,
    label: str,
    status: CheckStatus,
    message: str,
) -> None:
    checks.append(
        SchemaValidationCheck(
            schema_type=schema_type,
            field=field,
            label=label,
            status=status,
            message=message,
        )
    )


def _has_publisher_logo(schema: dict[str, Any]) -> bool:
    publisher = schema.get("publisher")
    if not isinstance(publisher, dict):
        return False
    logo = publisher.get("logo")
    if isinstance(logo, dict):
        return bool(logo.get("url"))
    return bool(logo)


def _validate_article_like(schema: dict[str, Any], checks: list[SchemaValidationCheck]) -> None:
    schema_type = schema.get("@type", "Article")

    if schema.get("headline"):
        _add_check(
            checks,
            schema_type=schema_type,
            field="headline",
            label="Naslov",
            status=CheckStatus.GOOD,
            message="Headline je prisutan.",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="headline",
            label="Naslov",
            status=CheckStatus.BAD,
            message="Google zahteva headline za članke.",
        )

    if schema.get("datePublished"):
        _add_check(
            checks,
            schema_type=schema_type,
            field="datePublished",
            label="Datum objave",
            status=CheckStatus.GOOD,
            message="datePublished je postavljen.",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="datePublished",
            label="Datum objave",
            status=CheckStatus.BAD,
            message="Nedostaje datePublished.",
        )

    author = schema.get("author")
    if isinstance(author, dict) and author.get("name"):
        _add_check(
            checks,
            schema_type=schema_type,
            field="author",
            label="Autor",
            status=CheckStatus.GOOD,
            message=f"Autor: {author.get('name')}.",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="author",
            label="Autor",
            status=CheckStatus.BAD,
            message="Google preporučuje author sa imenom.",
        )

    if _has_publisher_logo(schema):
        _add_check(
            checks,
            schema_type=schema_type,
            field="publisher.logo",
            label="Publisher logo",
            status=CheckStatus.GOOD,
            message="Publisher ima logo (ImageObject).",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="publisher.logo",
            label="Publisher logo",
            status=CheckStatus.OK,
            message="Dodajte logo organizacije za Article rich results.",
        )

    image = schema.get("image")
    if image:
        _add_check(
            checks,
            schema_type=schema_type,
            field="image",
            label="Slika",
            status=CheckStatus.GOOD,
            message="Slika članka je prisutna.",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="image",
            label="Slika",
            status=CheckStatus.OK,
            message="Google preporučuje sliku za Article rich results.",
        )


def _validate_webpage(schema: dict[str, Any], checks: list[SchemaValidationCheck]) -> None:
    schema_type = schema.get("@type", "WebPage")

    if schema.get("name") and schema.get("url"):
        _add_check(
            checks,
            schema_type=schema_type,
            field="name",
            label="Naziv stranice",
            status=CheckStatus.GOOD,
            message="WebPage ima name i url.",
        )
    else:
        _add_check(
            checks,
            schema_type=schema_type,
            field="name",
            label="Naziv stranice",
            status=CheckStatus.BAD,
            message="WebPage mora imati name i url.",
        )


def _validate_faqpage(
    schema: dict[str, Any],
    checks: list[SchemaValidationCheck],
) -> None:
    schema_type = "FAQPage"
    main_entity = schema.get("mainEntity")

    if not isinstance(main_entity, list) or not main_entity:
        _add_check(
            checks,
            schema_type=schema_type,
            field="mainEntity",
            label="FAQ pitanja",
            status=CheckStatus.BAD,
            message="FAQPage mora imati bar jedno pitanje u mainEntity.",
        )
        return

    valid_questions = 0
    for entity in main_entity:
        if not isinstance(entity, dict):
            continue
        answer = entity.get("acceptedAnswer")
        if entity.get("name") and isinstance(answer, dict) and answer.get("text"):
            valid_questions += 1

    if valid_questions >= 2:
        status = CheckStatus.GOOD
        message = f"Pronađeno {valid_questions} validnih FAQ stavki."
    elif valid_questions == 1:
        status = CheckStatus.OK
        message = "Pronađeno 1 FAQ stavka — dodajte još pitanja."
    else:
        status = CheckStatus.BAD
        message = "FAQ stavke nemaju ispravan Question/Answer format."

    _add_check(
        checks,
        schema_type=schema_type,
        field="mainEntity",
        label="FAQ pitanja",
        status=status,
        message=message,
    )


def _validate_organization(schema: dict[str, Any], checks: list[SchemaValidationCheck]) -> None:
    if schema.get("name") and schema.get("url"):
        _add_check(
            checks,
            schema_type="Organization",
            field="name",
            label="Organizacija",
            status=CheckStatus.GOOD,
            message="Organization ima name i url.",
        )
    else:
        _add_check(
            checks,
            schema_type="Organization",
            field="name",
            label="Organizacija",
            status=CheckStatus.BAD,
            message="Organization mora imati name i url.",
        )

    logo = schema.get("logo")
    if logo:
        _add_check(
            checks,
            schema_type="Organization",
            field="logo",
            label="Logo",
            status=CheckStatus.GOOD,
            message="Logo organizacije je prisutan.",
        )
    else:
        _add_check(
            checks,
            schema_type="Organization",
            field="logo",
            label="Logo",
            status=CheckStatus.OK,
            message="Preporučeno: dodajte logo organizacije.",
        )


def _validate_person(schema: dict[str, Any], checks: list[SchemaValidationCheck]) -> None:
    if schema.get("name"):
        _add_check(
            checks,
            schema_type="Person",
            field="name",
            label="Ime",
            status=CheckStatus.GOOD,
            message="Person ima name.",
        )
    else:
        _add_check(
            checks,
            schema_type="Person",
            field="name",
            label="Ime",
            status=CheckStatus.BAD,
            message="Person mora imati name.",
        )


def _validate_breadcrumb(schema: dict[str, Any], checks: list[SchemaValidationCheck]) -> None:
    items = schema.get("itemListElement")
    if not isinstance(items, list) or len(items) < 2:
        _add_check(
            checks,
            schema_type="BreadcrumbList",
            field="itemListElement",
            label="Breadcrumb stavke",
            status=CheckStatus.BAD,
            message="BreadcrumbList treba da ima bar 2 stavke.",
        )
        return

    valid = all(
        isinstance(item, dict)
        and item.get("position")
        and item.get("name")
        and item.get("item")
        for item in items
    )
    _add_check(
        checks,
        schema_type="BreadcrumbList",
        field="itemListElement",
        label="Breadcrumb stavke",
        status=CheckStatus.GOOD if valid else CheckStatus.BAD,
        message="Breadcrumb stavke su validne."
        if valid
        else "Svaka stavka mora imati position, name i item.",
    )


def _validate_single_schema(schema: dict[str, Any]) -> list[SchemaValidationCheck]:
    checks: list[SchemaValidationCheck] = []
    schema_type = schema.get("@type", "")

    if schema_type in {"Article", "BlogPosting"}:
        _validate_article_like(schema, checks)
    elif schema_type == "WebPage":
        _validate_webpage(schema, checks)
    elif schema_type == "FAQPage":
        _validate_faqpage(schema, checks)
    elif schema_type == "Organization":
        _validate_organization(schema, checks)
    elif schema_type == "Person":
        _validate_person(schema, checks)
    elif schema_type == "BreadcrumbList":
        _validate_breadcrumb(schema, checks)

    return checks


def validate_schema_graph(
    schemas: list[dict[str, Any]],
    *,
    content_object=None,
    requested_type: str = "",
) -> SchemaValidationResult:
    checks: list[SchemaValidationCheck] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    schema_types = [schema.get("@type", "") for schema in schemas if schema.get("@type")]

    for schema in schemas:
        checks.extend(_validate_single_schema(schema))

    if requested_type == "FAQPage" and "FAQPage" not in schema_types:
        faq_count = len(extract_faq_items(content_object)) if content_object else 0
        if faq_count == 0:
            warnings.append(
                "FAQPage je izabran, ali nema FAQ stavki u builderu "
                "(config.items ili naslov + tekst parovi)."
            )
            recommendations.append(
                "Dodajte FAQ blok u builder ili koristite H2–H4 naslov pa tekst ispod."
            )
        else:
            warnings.append("FAQPage nije generisan — proverite da li je sadržaj sačuvan.")

    if requested_type in {"Article", "BlogPosting"} and not any(
        t in schema_types for t in {"Article", "BlogPosting"}
    ):
        warnings.append("Article/BlogPosting šema nije generisana — proverite naslov i URL.")

    good = sum(1 for check in checks if check.status == CheckStatus.GOOD)
    ok = sum(1 for check in checks if check.status == CheckStatus.OK)
    bad = sum(1 for check in checks if check.status == CheckStatus.BAD)
    total = len(checks) or 1
    score = max(0, min(100, int(((good * 1.0) + (ok * 0.6) - (bad * 0.5)) / total * 100)))

    if bad == 0 and good >= ok:
        recommendations.append("Strukturirani podaci ispunjavaju Google preporuke.")
    elif bad:
        recommendations.append("Ispravite crvene stavke pre objave.")

    return SchemaValidationResult(
        score=score,
        checks=checks,
        warnings=warnings,
        recommendations=recommendations,
        schema_types=schema_types,
    )
