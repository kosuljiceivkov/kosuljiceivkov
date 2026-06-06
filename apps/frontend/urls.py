from django.urls import path

from . import cms_views, preview_views, views

app_name = "frontend"

urlpatterns = [
    path("", views.home, name="home"),
    path("usluge/", views.usluge, name="usluge"),
    path("kontakt/", views.kontakt, name="kontakt"),
    path("projekti/", cms_views.projekti, name="projekti"),
    path("blog/", cms_views.blog_list, name="blog"),
    path(
        "blog/kategorija/<path:category_path>/",
        cms_views.blog_category,
        name="blog_category",
    ),
    path("blog/<slug:slug>/", cms_views.blog_detail, name="blog_detail"),
    path(
        "pregled/cms/<int:pk>/",
        preview_views.preview_cms_page,
        name="admin_preview_cms",
    ),
    path(
        "pregled/blog/<int:pk>/",
        preview_views.preview_blog_post,
        name="admin_preview_blog",
    ),
]
