from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from apps.layout.builder_cache import get_cached_builder_html, set_cached_builder_html
from apps.layout.blocks.registry import get_block_render_context
from apps.layout.builder_services import get_builder_render_data

register = template.Library()


def _should_use_builder_cache(context, visible_only):
    if not visible_only:
        return False
    if context.get("is_admin_preview"):
        return False
    return True


def _render_builder_html(context, page_object, visible_only):
    request = context.get("request")
    render_data = get_builder_render_data(page_object, visible_only=visible_only)
    return render_to_string(
        "builder/page.html",
        {
            "sections": render_data["sections"],
            "page_object": page_object,
            "request": request,
            "has_carousel": render_data["has_carousel"],
        },
        request=request,
    )


@register.simple_tag(takes_context=True)
def render_page_builder(context, page_object, visible_only=True):
    """Renderuje page builder sa fragment kešom za javne stranice."""
    if page_object is None:
        return mark_safe(
            render_to_string(
                "builder/page.html",
                {
                    "sections": [],
                    "page_object": page_object,
                    "request": context.get("request"),
                    "has_carousel": False,
                },
                request=context.get("request"),
            )
        )

    use_cache = _should_use_builder_cache(context, visible_only)
    if use_cache and page_object.pk:
        cached_html = get_cached_builder_html(page_object, visible_only)
        if cached_html is not None:
            return mark_safe(cached_html)

    html = _render_builder_html(context, page_object, visible_only)

    if use_cache and page_object.pk:
        set_cached_builder_html(page_object, visible_only, html)

    return mark_safe(html)


@register.inclusion_tag("builder/block.html")
def render_builder_block(block):
    context = {"block": block}
    context.update(get_block_render_context(block))
    return context
