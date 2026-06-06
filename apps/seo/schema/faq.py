"""Izvlačenje FAQ parova iz page buildera za FAQPage šemu."""

from __future__ import annotations

from dataclasses import dataclass

from apps.layout.builder_models import Block
from apps.layout.builder_services import get_sections_for_object


@dataclass(frozen=True)
class FaqItem:
    question: str
    answer: str


def _faq_from_config(config: dict) -> list[FaqItem]:
    if not isinstance(config, dict):
        return []

    items: list[FaqItem] = []
    candidate_lists = []

    if config.get("type") in {"faq", "FAQ", "faq_block"}:
        candidate_lists.append(config.get("items") or config.get("faq_items") or [])

    if isinstance(config.get("faq"), list):
        candidate_lists.append(config["faq"])

    if isinstance(config.get("faq_items"), list):
        candidate_lists.append(config["faq_items"])

    for raw_items in candidate_lists:
        if not isinstance(raw_items, list):
            continue
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            question = (
                raw.get("question")
                or raw.get("q")
                or raw.get("title")
                or raw.get("name")
            )
            answer = raw.get("answer") or raw.get("a") or raw.get("text") or raw.get("content")
            if question and answer:
                items.append(
                    FaqItem(
                        question=str(question).strip(),
                        answer=str(answer).strip(),
                    )
                )
    return items


def _faq_from_heading_text_pairs(blocks: list[Block]) -> list[FaqItem]:
    """Heuristika: naslov (H2–H4) + sledeći tekstualni blok = pitanje/odgovor."""
    items: list[FaqItem] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if (
            block.block_type == Block.BlockType.HEADING
            and block.heading_level in {"h2", "h3", "h4"}
            and block.heading_text.strip()
        ):
            question = block.heading_text.strip()
            answer = ""
            next_index = index + 1
            while next_index < len(blocks):
                next_block = blocks[next_index]
                if next_block.block_type == Block.BlockType.TEXT and next_block.text_content.strip():
                    answer = next_block.text_content.strip()
                    break
                if next_block.block_type == Block.BlockType.HEADING:
                    break
                next_index += 1
            if answer:
                items.append(FaqItem(question=question, answer=answer))
                index = next_index
        index += 1
    return items


def extract_faq_items(page_object, *, visible_only: bool = True) -> list[FaqItem]:
    if page_object is None or not getattr(page_object, "pk", None):
        return []

    sections = get_sections_for_object(page_object, visible_only=visible_only)
    config_items: list[FaqItem] = []
    ordered_blocks: list[Block] = []

    for section in sections:
        for row in section.rows.all():
            for column in row.columns.all():
                for block in column.blocks.all():
                    ordered_blocks.append(block)
                    config_items.extend(_faq_from_config(block.config or {}))

    if config_items:
        return _dedupe_faq_items(config_items)

    return _dedupe_faq_items(_faq_from_heading_text_pairs(ordered_blocks))


def _dedupe_faq_items(items: list[FaqItem]) -> list[FaqItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[FaqItem] = []
    for item in items:
        key = (item.question.lower(), item.answer.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
