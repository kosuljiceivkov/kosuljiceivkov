"""Admin interfejs za SEO metapodatke."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from apps.seo.analysis_ui import (
    render_cornerstone_analysis_html,
    render_empty_analysis_html,
    render_image_seo_html,
    render_internal_linking_html,
    render_keyword_analysis_html,
    render_open_graph_preview_html,
    render_readability_analysis_html,
    render_robots_preview_html,
    render_schema_preview_html,
    render_serp_preview_html,
    render_twitter_preview_html,
    render_unified_scoring_html,
)
from apps.seo.image_seo import analyze_image_seo
from apps.seo.robots import build_robots_preview
from apps.seo.serp_preview import build_serp_preview
from apps.seo.unified_scoring import analyze_unified_seo
from apps.seo.cornerstone import analyze_cornerstone_content
from apps.seo.internal_linking import analyze_internal_linking
from apps.seo.keyword_analyzer import analyze_content_object
from apps.seo.open_graph import build_open_graph_tags, validate_og_image_file
from apps.seo.readability_analyzer import analyze_readability_for_object
from apps.seo.schema.engine import preview_schema_bundle
from apps.seo.twitter_card import build_twitter_card_tags
from apps.seo.models import SeoMetadata
from apps.seo.dashboard_actions import apply_bulk_action


class SeoAnalyzerAdminMixin:
    """Zajednički prikaz i live analiza u adminu."""

    keyword_readonly_field = "keyword_analysis_panel"
    readability_readonly_field = "readability_analysis_panel"
    og_preview_readonly_field = "og_preview_panel"
    og_image_validation_field = "og_image_validation_panel"
    twitter_preview_readonly_field = "twitter_preview_panel"
    twitter_image_validation_field = "twitter_image_validation_panel"
    schema_preview_readonly_field = "schema_preview_panel"
    internal_linking_readonly_field = "internal_linking_analysis_panel"
    cornerstone_readonly_field = "cornerstone_analysis_panel"
    unified_score_readonly_field = "unified_score_panel"
    serp_preview_readonly_field = "serp_preview_panel"
    robots_preview_readonly_field = "robots_preview_panel"
    image_seo_readonly_field = "image_seo_analysis_panel"

    class Media:
        css = {
            "all": (
                "admin/css/seo_analyzer.css",
                "admin/css/seo_og_preview.css",
                "admin/css/seo_twitter_preview.css",
                "admin/css/seo_schema_preview.css",
                "admin/css/seo_serp_preview.css",
            )
        }
        js = (
            "admin/js/seo_keyword_analyzer.js",
            "admin/js/seo_readability_analyzer.js",
            "admin/js/seo_serp_preview.js",
            "admin/js/seo_robots_preview.js",
            "admin/js/seo_image_seo.js",
            "admin/js/seo_og_preview.js",
            "admin/js/seo_twitter_preview.js",
            "admin/js/seo_schema_preview.js",
            "admin/js/seo_internal_linking.js",
            "admin/js/seo_cornerstone.js",
            "admin/js/seo_unified_score.js",
        )

    def _analyzer_config_html(self, *, api_name: str, content_type_id=None, object_id=None):
        return format_html(
            '<div class="seo-analyzer-config" data-seo-analyzer-api="{}" '
            'data-content-type-id="{}" data-object-id="{}" hidden></div>',
            reverse(f"admin:{api_name}"),
            content_type_id or "",
            object_id or "",
        )

    @admin.display(description="Analiza ključne reči")
    def keyword_analysis_panel(self, obj):
        if obj is None:
            return render_empty_analysis_html(
                "Sačuvajte objavu da biste videli analizu ključne reči."
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu, zatim unesite fokus ključnu reč za live analizu."
                ),
                self._analyzer_config_html(api_name="seo_keyword_analysis"),
            )

        result = analyze_content_object(content_object, obj, visible_only=False)
        return format_html(
            "{}{}",
            render_keyword_analysis_html(result),
            self._analyzer_config_html(
                api_name="seo_keyword_analysis",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Analiza čitljivosti")
    def readability_analysis_panel(self, obj):
        if obj is None:
            return render_empty_analysis_html(
                "Sačuvajte objavu da biste videli analizu čitljivosti.",
                analyzer_type="readability",
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste pokrenuli analizu čitljivosti.",
                    analyzer_type="readability",
                ),
                self._analyzer_config_html(api_name="seo_readability_analysis"),
            )

        result = analyze_readability_for_object(content_object, visible_only=False)
        return format_html(
            "{}{}",
            render_readability_analysis_html(result),
            self._analyzer_config_html(
                api_name="seo_readability_analysis",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Validacija OG slike")
    def og_image_validation_panel(self, obj):
        if obj is None:
            return "—"
        if not obj.og_image:
            return format_html(
                '<p class="seo-og-validation seo-og-validation--neutral">'
                "Nema prilagođene slike — koristi se istaknuta slika ili builder."
                "</p>"
            )
        result = validate_og_image_file(obj.og_image)
        messages = format_html_join("", "<li>{}</li>", ((msg,) for msg in result.messages))
        return format_html(
            '<ul class="seo-og-validation seo-og-validation--{}">{}</ul>',
            result.status.value,
            messages,
        )

    @admin.display(description="Open Graph pregled")
    def og_preview_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_open_graph_preview")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Unesite Open Graph podatke — pregled se ažurira dok kucate.",
                    analyzer_type="open_graph",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste videli pun pregled deljenja.",
                    analyzer_type="open_graph",
                ),
                config_html,
            )

        tags = build_open_graph_tags(content_object, metadata=obj, visible_only=False)
        return format_html(
            "{}{}",
            render_open_graph_preview_html(tags),
            self._analyzer_config_html(
                api_name="seo_open_graph_preview",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Validacija Twitter slike")
    def twitter_image_validation_panel(self, obj):
        if obj is None:
            return "—"
        if not obj.twitter_image:
            return format_html(
                '<p class="seo-twitter-validation seo-twitter-validation--neutral">'
                "Nema prilagođene slike — koristi se Open Graph ili istaknuta slika."
                "</p>"
            )
        result = validate_og_image_file(obj.twitter_image)
        messages = format_html_join("", "<li>{}</li>", ((msg,) for msg in result.messages))
        return format_html(
            '<ul class="seo-twitter-validation seo-twitter-validation--{}">{}</ul>',
            result.status.value,
            messages,
        )

    @admin.display(description="Twitter Card pregled")
    def twitter_preview_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_twitter_card_preview")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Unesite Twitter podatke — pregled se ažurira dok kucate.",
                    analyzer_type="twitter",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste videli pun Twitter pregled.",
                    analyzer_type="twitter",
                ),
                config_html,
            )

        og_tags = build_open_graph_tags(content_object, metadata=obj, visible_only=False)
        tags = build_twitter_card_tags(
            content_object,
            metadata=obj,
            og_tags=og_tags,
            visible_only=False,
        )
        return format_html(
            "{}{}",
            render_twitter_preview_html(tags),
            self._analyzer_config_html(
                api_name="seo_twitter_card_preview",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )


    @admin.display(description="Schema.org pregled")
    def schema_preview_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_schema_preview")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Izaberite tip šeme — JSON-LD pregled se ažurira dok menjate podatke.",
                    analyzer_type="schema",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste videli JSON-LD i Google validaciju.",
                    analyzer_type="schema",
                ),
                config_html,
            )

        request = getattr(self, "_current_request", None)
        _, payloads, validation = preview_schema_bundle(
            request,
            content_object,
            metadata=obj,
            schema_type=obj.schema_type or None,
            visible_only=False,
        )
        return format_html(
            "{}{}",
            render_schema_preview_html(
                schema_types=validation.schema_types,
                json_payloads=payloads,
                validation=validation,
            ),
            self._analyzer_config_html(
                api_name="seo_schema_preview",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Interni linkovi")
    def internal_linking_analysis_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_internal_linking_analysis")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte blog objavu da biste videli preporuke internih linkova.",
                    analyzer_type="internal_linking",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste pokrenuli analizu internih linkova.",
                    analyzer_type="internal_linking",
                ),
                config_html,
            )

        result = analyze_internal_linking(content_object, obj, visible_only=False)
        return format_html(
            "{}{}",
            render_internal_linking_html(result),
            self._analyzer_config_html(
                api_name="seo_internal_linking_analysis",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Analiza slika")
    def image_seo_analysis_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_image_seo_analysis")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste videli analizu slika.",
                    analyzer_type="image_seo",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu i dodajte slike u builder.",
                    analyzer_type="image_seo",
                ),
                config_html,
            )

        result = analyze_image_seo(content_object, obj, visible_only=False)
        return format_html(
            "{}{}",
            render_image_seo_html(result),
            self._analyzer_config_html(
                api_name="seo_image_seo_analysis",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Google SERP pregled")
    def serp_preview_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_serp_preview")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Unesite SEO naslov i meta opis — pregled se ažurira dok kucate.",
                    analyzer_type="serp",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        request = getattr(self, "_current_request", None)

        if content_object is None or not getattr(content_object, "pk", None):
            preview = build_serp_preview(None, request, obj)
            return format_html(
                "{}{}",
                render_serp_preview_html(preview),
                config_html,
            )

        preview = build_serp_preview(content_object, request, obj)
        return format_html(
            "{}{}",
            render_serp_preview_html(preview),
            self._analyzer_config_html(
                api_name="seo_serp_preview",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Robots meta tag")
    def robots_preview_panel(self, obj):
        preview = build_robots_preview(obj if obj and getattr(obj, "pk", None) else None)
        return render_robots_preview_html(preview)

    @admin.display(description="SEO ocena")
    def unified_score_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_unified_score")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste videli ukupnu SEO ocenu.",
                    analyzer_type="unified_score",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste pokrenuli unified SEO scoring.",
                    analyzer_type="unified_score",
                ),
                config_html,
            )

        request = getattr(self, "_current_request", None)
        result = analyze_unified_seo(content_object, obj, request=request, visible_only=False)
        return format_html(
            "{}{}",
            render_unified_scoring_html(result),
            self._analyzer_config_html(
                api_name="seo_unified_score",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )

    @admin.display(description="Cornerstone analiza")
    def cornerstone_analysis_panel(self, obj):
        config_html = self._analyzer_config_html(api_name="seo_cornerstone_analysis")

        if obj is None:
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte blog objavu da biste videli cornerstone analizu.",
                    analyzer_type="cornerstone",
                ),
                config_html,
            )

        content_object = getattr(obj, "content_object", None)
        if content_object is None or not getattr(content_object, "pk", None):
            return format_html(
                "{}{}",
                render_empty_analysis_html(
                    "Sačuvajte objavu da biste pokrenuli cornerstone analizu.",
                    analyzer_type="cornerstone",
                ),
                config_html,
            )

        result = analyze_cornerstone_content(content_object, obj, visible_only=False)
        return format_html(
            "{}{}",
            render_cornerstone_analysis_html(result),
            self._analyzer_config_html(
                api_name="seo_cornerstone_analysis",
                content_type_id=obj.content_type_id,
                object_id=obj.object_id,
            ),
        )


class SeoScoreListFilter(admin.SimpleListFilter):
    title = "SEO ocena"
    parameter_name = "seo_score_band"

    def lookups(self, request, model_admin):
        return (
            ("low", "Niska (< 40)"),
            ("medium", "Srednja (40–69)"),
            ("high", "Dobra (≥ 70)"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "low":
            return queryset.filter(seo_score__lt=40)
        if value == "medium":
            return queryset.filter(seo_score__gte=40, seo_score__lt=70)
        if value == "high":
            return queryset.filter(seo_score__gte=70)
        return queryset


class MissingSeoTitleFilter(admin.SimpleListFilter):
    title = "SEO naslov"
    parameter_name = "missing_seo_title"

    def lookups(self, request, model_admin):
        return (("yes", "Nedostaje"),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(seo_title="")
        return queryset


class MissingMetaDescriptionFilter(admin.SimpleListFilter):
    title = "Meta opis"
    parameter_name = "missing_meta_description"

    def lookups(self, request, model_admin):
        return (("yes", "Nedostaje"),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(meta_description="")
        return queryset


@admin.action(description="Preračunaj SEO ocene")
def recalculate_seo_scores_action(modeladmin, request, queryset):
    apply_bulk_action(
        request,
        "recalculate_scores",
        list(queryset.values_list("pk", flat=True)),
    )


@admin.action(description="Označi kao cornerstone")
def mark_cornerstone_action(modeladmin, request, queryset):
    apply_bulk_action(
        request,
        "mark_cornerstone",
        list(queryset.values_list("pk", flat=True)),
    )


@admin.action(description="Ukloni cornerstone")
def unmark_cornerstone_action(modeladmin, request, queryset):
    apply_bulk_action(
        request,
        "unmark_cornerstone",
        list(queryset.values_list("pk", flat=True)),
    )


@admin.action(description="Postavi noindex")
def set_noindex_action(modeladmin, request, queryset):
    apply_bulk_action(
        request,
        "set_noindex",
        list(queryset.values_list("pk", flat=True)),
    )


@admin.action(description="Postavi index")
def set_index_action(modeladmin, request, queryset):
    apply_bulk_action(
        request,
        "set_index",
        list(queryset.values_list("pk", flat=True)),
    )


class SeoMetadataInline(SeoAnalyzerAdminMixin, GenericStackedInline):
    """Yoast-style SEO panel u editoru bloga i CMS stranica."""

    model = SeoMetadata
    extra = 0
    max_num = 1
    can_delete = True
    classes = ("seo-metadata-inline",)
    verbose_name = "SEO"
    verbose_name_plural = "SEO"
    readonly_fields = (
        SeoAnalyzerAdminMixin.keyword_readonly_field,
        SeoAnalyzerAdminMixin.readability_readonly_field,
        SeoAnalyzerAdminMixin.og_image_validation_field,
        SeoAnalyzerAdminMixin.og_preview_readonly_field,
        SeoAnalyzerAdminMixin.twitter_image_validation_field,
        SeoAnalyzerAdminMixin.twitter_preview_readonly_field,
        SeoAnalyzerAdminMixin.schema_preview_readonly_field,
        SeoAnalyzerAdminMixin.internal_linking_readonly_field,
        SeoAnalyzerAdminMixin.cornerstone_readonly_field,
        SeoAnalyzerAdminMixin.unified_score_readonly_field,
        SeoAnalyzerAdminMixin.serp_preview_readonly_field,
        SeoAnalyzerAdminMixin.robots_preview_readonly_field,
        SeoAnalyzerAdminMixin.image_seo_readonly_field,
    )
    fieldsets = (
        (
            "SEO ocena",
            {
                "fields": (SeoAnalyzerAdminMixin.unified_score_readonly_field,),
                "description": (
                    "Ukupna SEO ocena (0–100) sa kategorijama, preporukama i JSON izlazom."
                ),
            },
        ),
        (
            "Osnovno",
            {
                "fields": (
                    "seo_title",
                    "meta_description",
                    SeoAnalyzerAdminMixin.serp_preview_readonly_field,
                    "focus_keyword",
                    "secondary_keywords",
                    "canonical_url",
                ),
                "description": (
                    "Google SERP pregled se ažurira uživo dok menjate naslov i meta opis."
                ),
            },
        ),
        (
            "Robots",
            {
                "fields": (
                    "robots_index",
                    "robots_follow",
                    "robots_nosnippet",
                    "robots_noarchive",
                    "robots_max_image_preview",
                    SeoAnalyzerAdminMixin.robots_preview_readonly_field,
                ),
                "description": (
                    "Kontrolišite indeksiranje, praćenje linkova i prikaz u rezultatima pretrage. "
                    "Meta tag ispod se ažurira uživo."
                ),
            },
        ),
        (
            "Open Graph",
            {
                "fields": (
                    "og_title",
                    "og_description",
                    "og_image",
                    SeoAnalyzerAdminMixin.og_image_validation_field,
                    "og_type",
                    "og_url",
                    SeoAnalyzerAdminMixin.og_preview_readonly_field,
                ),
                "description": (
                    "Pregled kako će link izgledati na Facebook-u i LinkedIn-u. "
                    "Prazna polja koriste SEO naslov, meta opis i kanonski URL."
                ),
            },
        ),
        (
            "Twitter",
            {
                "fields": (
                    "twitter_title",
                    "twitter_description",
                    "twitter_image",
                    SeoAnalyzerAdminMixin.twitter_image_validation_field,
                    "twitter_card",
                    SeoAnalyzerAdminMixin.twitter_preview_readonly_field,
                ),
                "description": (
                    "Pregled Twitter / X Card-a. Prazna polja koriste Open Graph vrednosti."
                ),
            },
        ),
        (
            "Schema.org",
            {
                "fields": (
                    "schema_type",
                    "breadcrumb_title",
                    SeoAnalyzerAdminMixin.schema_preview_readonly_field,
                ),
                "description": (
                    "JSON-LD za Google Rich Results: Article, BlogPosting, FAQPage, "
                    "WebPage, Person, Organization i BreadcrumbList."
                ),
            },
        ),
        (
            "Cornerstone sadržaj",
            {
                "fields": (
                    "is_cornerstone",
                    SeoAnalyzerAdminMixin.cornerstone_readonly_field,
                ),
                "description": (
                    "Označite glavne tematske članke. Supporting objave treba da linkuju "
                    "ka cornerstone-u; sistem prikazuje orphan upozorenja i preporuke klastera."
                ),
            },
        ),
        (
            "Analiza ključne reči",
            {
                "fields": (SeoAnalyzerAdminMixin.keyword_readonly_field,),
                "description": (
                    "Zeleno = odlično · Žuto = može bolje · Crveno = potrebno poboljšanje"
                ),
            },
        ),
        (
            "Analiza čitljivosti",
            {
                "fields": (SeoAnalyzerAdminMixin.readability_readonly_field,),
                "description": (
                    "Provera dužine rečenica i pasusa, pasiva, prelaznih reči, "
                    "naslova i težine čitanja."
                ),
            },
        ),
        (
            "Analiza slika",
            {
                "fields": (SeoAnalyzerAdminMixin.image_seo_readonly_field,),
                "description": (
                    "Alt tekst, nazivi fajlova, dimenzije i kompresija — "
                    "sačuvajte objavu nakon izmena u builderu."
                ),
            },
        ),
        (
            "Interni linkovi",
            {
                "fields": (SeoAnalyzerAdminMixin.internal_linking_readonly_field,),
                "description": (
                    "Preporuke povezivanja ka povezanim člancima, anchor tekst "
                    "i ocena kvaliteta internog linkovanja."
                ),
            },
        ),
    )


@admin.register(SeoMetadata)
class SeoMetadataAdmin(SeoAnalyzerAdminMixin, admin.ModelAdmin):
    actions = (
        recalculate_seo_scores_action,
        mark_cornerstone_action,
        unmark_cornerstone_action,
        set_noindex_action,
        set_index_action,
    )

    def has_module_permission(self, request):
        """Sakrij iz levog menija — SEO se uređuje u editoru objave (fioka SEO)."""
        return False

    list_display = (
        "content_object",
        "seo_title",
        "focus_keyword",
        "keyword_score",
        "readability_score",
        "internal_linking_score",
        "image_seo_score",
        "seo_score",
        "is_cornerstone",
        "updated_at",
    )
    list_filter = (
        SeoScoreListFilter,
        MissingSeoTitleFilter,
        MissingMetaDescriptionFilter,
        "is_cornerstone",
        "robots_index",
        "schema_type",
    )
    search_fields = (
        "seo_title",
        "meta_description",
        "focus_keyword",
        "secondary_keywords",
    )
    readonly_fields = (
        SeoAnalyzerAdminMixin.keyword_readonly_field,
        SeoAnalyzerAdminMixin.readability_readonly_field,
        SeoAnalyzerAdminMixin.og_image_validation_field,
        SeoAnalyzerAdminMixin.og_preview_readonly_field,
        SeoAnalyzerAdminMixin.twitter_image_validation_field,
        SeoAnalyzerAdminMixin.twitter_preview_readonly_field,
        SeoAnalyzerAdminMixin.schema_preview_readonly_field,
        SeoAnalyzerAdminMixin.internal_linking_readonly_field,
        SeoAnalyzerAdminMixin.cornerstone_readonly_field,
        SeoAnalyzerAdminMixin.unified_score_readonly_field,
        SeoAnalyzerAdminMixin.serp_preview_readonly_field,
        SeoAnalyzerAdminMixin.robots_preview_readonly_field,
        SeoAnalyzerAdminMixin.image_seo_readonly_field,
        "seo_score",
        "keyword_score",
        "readability_score",
        "internal_linking_score",
        "image_seo_score",
        "updated_at",
    )
    fieldsets = SeoMetadataInline.fieldsets + (
        (
            "Ocene",
            {
                "fields": (
                    "keyword_score",
                    "readability_score",
                    "internal_linking_score",
                    "image_seo_score",
                    "seo_score",
                ),
            },
        ),
        (
            "Sistem",
            {
                "fields": ("content_type", "object_id", "updated_at"),
            },
        ),
    )
