"""SEO slike — istaknuta slika ili prva slika iz buildera."""

from apps.core.mixins import CMSMetaMixin

from .builder_images import get_first_builder_image_field


def get_image_dimensions(image_field):
    if not image_field or not getattr(image_field, "name", ""):
        return None, None

    width = getattr(image_field, "width", None)
    height = getattr(image_field, "height", None)
    if width and height:
        return int(width), int(height)
    return None, None


def get_page_seo_image(page_object, request=None, *, visible_only=True):
    """
    Vraća (apsolutni_url, širina, visina).
    Prvo istaknuta slika, zatim prva slika iz page buildera.
    """
    featured = getattr(page_object, "featured_image", None)
    if featured and getattr(featured, "name", ""):
        url = CMSMetaMixin.resolve_absolute_url(request, featured.url)
        width, height = get_image_dimensions(featured)
        return url, width, height

    builder_image = get_first_builder_image_field(page_object, visible_only=visible_only)
    if builder_image and getattr(builder_image, "name", ""):
        url = CMSMetaMixin.resolve_absolute_url(request, builder_image.url)
        width, height = get_image_dimensions(builder_image)
        return url, width, height

    return "", None, None


def apply_seo_image_to_context(page_object, context, request, *, visible_only=True):
    """Dopunjava SEO kontekst slikom i dimenzijama za Open Graph."""
    image_url, width, height = get_page_seo_image(
        page_object,
        request,
        visible_only=visible_only,
    )
    if not image_url:
        return context

    context["og_image"] = image_url
    context["twitter_image"] = image_url
    context["twitter_card"] = "summary_large_image"
    if width and height:
        context["og_image_width"] = width
        context["og_image_height"] = height
    return context
