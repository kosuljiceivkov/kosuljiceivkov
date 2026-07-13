"""Strukturisano logovanje za blog document admin API."""

from __future__ import annotations

import logging

logger = logging.getLogger("apps.blog.admin_api")


def log_page_save_validation_error(*, post_id: int, user_id: int | None, messages: list[str]) -> None:
    logger.warning(
        "page_save_validation_error post_id=%s user_id=%s errors=%s",
        post_id,
        user_id,
        messages,
    )


def log_page_save_version_conflict(
    *,
    post_id: int,
    user_id: int | None,
    expected: int,
    actual: int,
) -> None:
    logger.warning(
        "page_save_version_conflict post_id=%s user_id=%s expected=%s actual=%s",
        post_id,
        user_id,
        expected,
        actual,
    )


def log_page_save_invalid_json(*, post_id: int, user_id: int | None) -> None:
    logger.warning(
        "page_save_invalid_json post_id=%s user_id=%s",
        post_id,
        user_id,
    )


def log_page_save_unexpected_error(*, post_id: int, user_id: int | None, exc: Exception) -> None:
    logger.exception(
        "page_save_unexpected_error post_id=%s user_id=%s",
        post_id,
        user_id,
        exc_info=exc,
    )


def log_upload_failure(*, post_id: int, user_id: int | None, code: str) -> None:
    logger.warning(
        "document_upload_failure post_id=%s user_id=%s code=%s",
        post_id,
        user_id,
        code,
    )


def log_upload_unexpected_error(*, post_id: int, user_id: int | None, exc: Exception) -> None:
    logger.exception(
        "document_upload_unexpected_error post_id=%s user_id=%s",
        post_id,
        user_id,
        exc_info=exc,
    )
