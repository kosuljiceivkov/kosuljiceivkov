from django import template

register = template.Library()


@register.inclusion_tag("partials/carousel_static_image.html", takes_context=False)
def carousel_static_image(
    image_path,
    css_class="",
    alt="",
    width=None,
    height=None,
    priority=False,
    sizes="",
):
    """Statička WebP slika — width/height za CLS i adaptivni karusel."""
    return {
        "image_path": image_path,
        "css_class": css_class,
        "alt": alt,
        "width": width,
        "height": height,
        "priority": priority,
        "sizes": sizes,
    }
