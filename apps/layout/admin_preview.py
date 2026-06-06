from django.utils.html import format_html
from django.utils.safestring import mark_safe


def render_image_preview(image_field, *, max_height=56):
    if not image_field:
        return "—"
    return format_html(
        '<img src="{}" alt="" class="builder-admin-thumb" '
        'style="max-height:{}px;border-radius:4px;">',
        image_field.url,
        max_height,
    )


def render_carousel_preview(carousel):
    if carousel is None:
        return mark_safe('<p class="builder-admin-preview-empty">Nema podešavanja karusela.</p>')

    items = list(carousel.items.all()[:6])
    if not items:
        return mark_safe(
            '<p class="builder-admin-preview-empty">Dodajte stavke karusela ispod.</p>'
        )

    slides_html = []
    for index, item in enumerate(items):
        active = " is-active" if index == 0 else ""
        overlay = ""
        if item.title:
            overlay += f"<strong>{item.title}</strong>"
        if item.description:
            overlay += f"<span>{item.description[:80]}</span>"
        if item.button_text:
            overlay += f'<em class="builder-admin-preview-btn">{item.button_text}</em>'

        overlay_block = (
            f'<div class="builder-admin-preview-overlay">{overlay}</div>' if overlay else ""
        )
        slides_html.append(
            format_html(
                '<figure class="builder-admin-preview-slide{}">'
                '<img src="{}" alt="">{}</figure>',
                active,
                item.image.url,
                mark_safe(overlay_block),
            )
        )

    extra = ""
    if carousel.item_count > len(items):
        extra = format_html(
            '<p class="builder-admin-preview-more">+ još {} stavki</p>',
            carousel.item_count - len(items),
        )

    return format_html(
        '<div class="builder-admin-carousel-preview" data-preview-carousel>'
        '<div class="builder-admin-carousel-preview__track">{}</div>'
        '<p class="builder-admin-preview-meta">{} stavki · autoplay: {} · strelice: {} · tačkice: {}</p>'
        "{}</div>",
        mark_safe("".join(slides_html)),
        carousel.item_count,
        "da" if carousel.autoplay else "ne",
        "da" if carousel.show_arrows else "ne",
        "da" if carousel.show_dots else "ne",
        mark_safe(extra),
    )
