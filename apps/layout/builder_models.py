from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.storage_aliases import blog_images_storage, project_videos_storage
from apps.layout.validators import validate_css_color


class OrderedModel(models.Model):
    """Zajedničko polje za sortiranje u adminu (drag-and-drop)."""

    order = models.PositiveIntegerField("Redosled", default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["order", "pk"]


class Section(OrderedModel):
    """Sekcija page buildera — pripada CMSPage ili BlogPost."""

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tip sadržaja",
    )
    object_id = models.PositiveBigIntegerField("ID sadržaja")
    content_object = GenericForeignKey("content_type", "object_id")

    admin_label = models.CharField(
        "Admin oznaka",
        max_length=120,
        blank=True,
        help_text="Interni naziv u adminu (nije vidljiv posetiocima).",
    )
    is_visible = models.BooleanField("Vidljivo", default=True)

    background_color = models.CharField(
        "Boja pozadine",
        max_length=32,
        blank=True,
        help_text="Hex (#f5f5f5) ili CSS boja. Prazno = podrazumevano.",
    )
    padding_top = models.CharField(
        "Razmak gore",
        max_length=16,
        choices=[
            ("none", "Bez"),
            ("sm", "Malo"),
            ("md", "Srednje"),
            ("lg", "Veliko"),
        ],
        default="md",
    )
    padding_bottom = models.CharField(
        "Razmak dole",
        max_length=16,
        choices=[
            ("none", "Bez"),
            ("sm", "Malo"),
            ("md", "Srednje"),
            ("lg", "Veliko"),
        ],
        default="md",
    )
    container_width = models.CharField(
        "Širina kontejnera",
        max_length=16,
        choices=[
            ("contained", "U okviru kontejnera"),
            ("full", "Puna širina"),
        ],
        default="contained",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Sekcija"
        verbose_name_plural = "Sekcije"

    def __str__(self):
        if self.admin_label:
            return f"Sekcija: {self.admin_label}"
        if self.order or self.pk:
            return f"Sekcija #{self.order + 1 if self.order is not None else self.pk}"
        return "Sekcija"

    def clean(self):
        super().clean()
        try:
            validate_css_color(self.background_color)
        except ValidationError as exc:
            raise ValidationError({"background_color": exc.messages}) from exc


class Row(OrderedModel):
    """Red unutar sekcije."""

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="rows",
        verbose_name="Sekcija",
    )
    gap = models.CharField(
        "Razmak između kolona",
        max_length=16,
        choices=[
            ("none", "Bez"),
            ("sm", "Malo"),
            ("md", "Srednje"),
            ("lg", "Veliko"),
        ],
        default="md",
    )
    vertical_align = models.CharField(
        "Vertikalno poravnanje",
        max_length=16,
        choices=[
            ("top", "Gore"),
            ("center", "Centar"),
            ("bottom", "Dole"),
        ],
        default="top",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Red"
        verbose_name_plural = "Redovi"

    def __str__(self):
        index = (self.order + 1) if self.order is not None else (self.pk or "?")
        return f"Red #{index}"


class Column(OrderedModel):
    """Kolona unutar reda."""

    row = models.ForeignKey(
        Row,
        on_delete=models.CASCADE,
        related_name="columns",
        verbose_name="Red",
    )
    desktop_width = models.PositiveSmallIntegerField(
        "Širina na desktopu",
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Desktop (≥1200px). 12 = puna širina, 6 = pola, 4 = trećina.",
    )
    tablet_width = models.PositiveSmallIntegerField(
        "Širina na tabletu",
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Tablet (768–1199px).",
    )
    mobile_width = models.PositiveSmallIntegerField(
        "Širina na mobilnom",
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Mobil (≤767px).",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Kolona"
        verbose_name_plural = "Kolone"

    @property
    def width(self):
        """Zadržava kompatibilnost sa starijim kodom."""
        return self.desktop_width

    @width.setter
    def width(self, value):
        self.desktop_width = value

    def __str__(self):
        return (
            f"Kolona D{self.desktop_width}/ T{self.tablet_width}/ M{self.mobile_width}"
        )

    def get_responsive_css_classes(self):
        return (
            f"col-mobile-{self.mobile_width} "
            f"col-tablet-{self.tablet_width} "
            f"col-desktop-{self.desktop_width}"
        )

    def clean(self):
        super().clean()
        if not self.row_id:
            return

        siblings = Column.objects.filter(row_id=self.row_id)
        if self.pk:
            siblings = siblings.exclude(pk=self.pk)

        breakpoint_fields = (
            ("desktop_width", "desktop_width", "desktopu"),
            ("tablet_width", "tablet_width", "tabletu"),
            ("mobile_width", "mobile_width", "mobilnom"),
        )
        errors = {}
        for field_name, attr_name, label in breakpoint_fields:
            own_width = getattr(self, attr_name)
            total_width = sum(getattr(column, attr_name) for column in siblings) + own_width
            if total_width > 12:
                errors[field_name] = (
                    f"Zbir širina kolona u redu na {label} ne sme biti veći od 12. "
                    f"Trenutno: {total_width}."
                )

        if errors:
            raise ValidationError(errors)


class Block(OrderedModel):
    """Blok sadržaja unutar kolone."""

    class BlockType(models.TextChoices):
        HEADING = "heading", "Naslov"
        TEXT = "text", "Tekst"
        IMAGE = "image", "Slika"
        BUTTON = "button", "Dugme"
        VIDEO = "video", "Video"
        SPACER = "spacer", "Razmak"
        DIVIDER = "divider", "Linija"
        GALLERY = "gallery", "Galerija"
        CAROUSEL = "carousel", "Karusel"

    class HeadingLevel(models.TextChoices):
        H1 = "h1", "H1"
        H2 = "h2", "H2"
        H3 = "h3", "H3"
        H4 = "h4", "H4"
        H5 = "h5", "H5"
        H6 = "h6", "H6"

    class TextAlign(models.TextChoices):
        LEFT = "left", "Levo"
        CENTER = "center", "Centar"
        RIGHT = "right", "Desno"

    class ButtonStyle(models.TextChoices):
        PRIMARY = "primary", "Primarno"
        OUTLINE = "outline", "Obrub"
        DARK = "dark", "Tamno"

    class DividerStyle(models.TextChoices):
        SOLID = "solid", "Puna"
        DASHED = "dashed", "Isprekidana"
        DOTTED = "dotted", "Tačkasta"

    class VideoSource(models.TextChoices):
        EMBED = "embed", "Embed URL (YouTube/Vimeo)"
        FILE = "file", "Video fajl"

    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Kolona",
    )
    block_type = models.CharField(
        "Tip bloka",
        max_length=20,
        choices=BlockType.choices,
        default=BlockType.TEXT,
    )

    # Heading
    heading_text = models.CharField("Tekst naslova", max_length=255, blank=True)
    heading_level = models.CharField(
        "Nivo naslova",
        max_length=2,
        choices=HeadingLevel.choices,
        default=HeadingLevel.H2,
    )
    heading_align = models.CharField(
        "Poravnanje naslova",
        max_length=10,
        choices=TextAlign.choices,
        default=TextAlign.LEFT,
    )

    # Text
    text_content = models.TextField("Tekst", blank=True)
    text_align = models.CharField(
        "Poravnanje teksta",
        max_length=10,
        choices=TextAlign.choices,
        default=TextAlign.LEFT,
    )

    # Image
    image = models.ImageField(
        "Slika",
        upload_to="builder/images/%Y/%m/",
        storage=blog_images_storage,
        blank=True,
    )
    image_alt = models.CharField("Alt tekst slike", max_length=255, blank=True)
    image_caption = models.CharField("Opis slike", max_length=255, blank=True)
    image_link_url = models.URLField("Link slike", blank=True)

    # Button
    button_label = models.CharField("Tekst dugmeta", max_length=120, blank=True)
    button_url = models.URLField("URL dugmeta", blank=True)
    button_style = models.CharField(
        "Stil dugmeta",
        max_length=16,
        choices=ButtonStyle.choices,
        default=ButtonStyle.PRIMARY,
    )
    button_open_new_tab = models.BooleanField("Otvori u novom tabu", default=False)

    # Video
    video_source = models.CharField(
        "Izvor videa",
        max_length=10,
        choices=VideoSource.choices,
        default=VideoSource.EMBED,
    )
    video_embed_url = models.URLField(
        "Embed URL",
        blank=True,
        help_text="YouTube ili Vimeo embed link.",
    )
    video_file = models.FileField(
        "Video fajl",
        upload_to="builder/videos/%Y/%m/",
        storage=project_videos_storage,
        blank=True,
    )
    video_poster = models.ImageField(
        "Poster slike",
        upload_to="builder/posters/%Y/%m/",
        storage=blog_images_storage,
        blank=True,
    )

    # Spacer
    spacer_height = models.PositiveSmallIntegerField(
        "Visina razmaka (px)",
        default=32,
    )
    spacer_height_mobile = models.PositiveSmallIntegerField(
        "Visina razmaka na mobilnom (px)",
        blank=True,
        null=True,
    )

    # Divider
    divider_style = models.CharField(
        "Stil linije",
        max_length=10,
        choices=DividerStyle.choices,
        default=DividerStyle.SOLID,
    )
    divider_width = models.CharField(
        "Širina linije",
        max_length=16,
        choices=[
            ("full", "Puna"),
            ("contained", "U okviru"),
        ],
        default="contained",
    )

    config = models.JSONField(
        "Konfiguracija bloka",
        default=dict,
        blank=True,
        help_text="JSON podaci za nove tipove blokova (FAQ, cene, mape…).",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Blok"
        verbose_name_plural = "Blokovi"

    def __str__(self):
        type_label = self.get_block_type_display()
        if self.block_type == self.BlockType.HEADING and self.heading_text:
            return f"{type_label}: {self.heading_text}"
        if self.block_type == self.BlockType.BUTTON and self.button_label:
            return f"{type_label}: {self.button_label}"
        if self.block_type == self.BlockType.CAROUSEL:
            return "Karusel"
        return f"{type_label} #{self.pk}" if self.pk else type_label

    def get_template_name(self):
        from apps.layout.blocks.registry import get_block_template_name

        return get_block_template_name(self.block_type)

    def get_plugin(self):
        from apps.layout.blocks.registry import get_block_plugin

        return get_block_plugin(self.block_type)

    def clean(self):
        super().clean()
        from apps.layout.blocks.registry import validate_block

        validate_block(self)


class BlockGalleryImage(OrderedModel):
    """Slika u galeriji bloka."""

    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name="Blok",
    )
    image = models.ImageField(
        "Slika",
        upload_to="builder/gallery/%Y/%m/",
        storage=blog_images_storage,
    )
    alt_text = models.CharField("Alt tekst", max_length=255, blank=True)
    caption = models.CharField("Opis", max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Slika galerije"
        verbose_name_plural = "Slike galerije"

    def __str__(self):
        return self.caption or self.alt_text or f"Slika #{self.pk}"


class Carousel(models.Model):
    """Podešavanja karusela — povezano 1:1 sa Block tipa karusel."""

    block = models.OneToOneField(
        Block,
        on_delete=models.CASCADE,
        related_name="carousel",
        verbose_name="Blok",
    )
    autoplay = models.BooleanField("Automatska reprodukcija", default=True)
    show_arrows = models.BooleanField("Strelice za navigaciju", default=True)
    show_dots = models.BooleanField("Tačkice (paginacija)", default=True)
    speed_ms = models.PositiveSmallIntegerField(
        "Brzina tranzicije (ms)",
        default=500,
        help_text="Trajanje animacije prelaska između slajdova.",
    )
    interval_seconds = models.PositiveSmallIntegerField(
        "Interval automatske reprodukcije (sek)",
        default=5,
    )

    class Meta:
        verbose_name = "Karusel"
        verbose_name_plural = "Karuseli"

    def __str__(self):
        return f"Karusel (blok #{self.block_id})"

    @property
    def item_count(self):
        return self.items.count()


class CarouselItem(OrderedModel):
    """
    Stavka karusela.
    Podržava: samo sliku, sliku + naslov, sliku + tekst, sliku + dugme.
    """

    carousel = models.ForeignKey(
        Carousel,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Karusel",
    )
    image = models.ImageField(
        "Slika",
        upload_to="builder/carousel/%Y/%m/",
        storage=blog_images_storage,
    )
    alt_text = models.CharField("Alt tekst", max_length=255, blank=True)
    title = models.CharField("Naslov", max_length=255, blank=True)
    description = models.TextField("Opis", blank=True)
    button_text = models.CharField("Tekst dugmeta", max_length=120, blank=True)
    button_url = models.URLField("URL dugmeta", blank=True)
    button_open_new_tab = models.BooleanField("Otvori dugme u novom tabu", default=False)

    class Meta(OrderedModel.Meta):
        verbose_name = "Stavka karusela"
        verbose_name_plural = "Stavke karusela"

    def __str__(self):
        return self.title or self.alt_text or f"Stavka #{self.pk}"

    @property
    def has_overlay_content(self):
        return bool(self.title or self.description or self.button_text)

    @property
    def has_button(self):
        return bool(self.button_text and self.button_url)

