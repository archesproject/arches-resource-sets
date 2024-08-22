from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

urlpatterns = [
    path("", include("arches.urls")),
    path("api/resource_sets/", ListsView.as_view(), name="resource_sets"),
    path(
        "api/resource_set/<uuid:list_id>/",
        ListView.as_view(),
        name="resource_set",
    ),
    path(
        "api/resource_set/<uuid:list_id>/add",
        ListView.as_view(),
        name="resource_set_add",
    ),
    path(
        "api/resource_set/<uuid:list_id>/delete",
        ListView.as_view(),
        name="resource_set_add",
    ),
    path(
        "api/resource_set/<uuid:list_id>/resources/",
        ListView.as_view(),
        name="resource_set",
    ),
    path(
        "api/resource_set/<uuid:list_id>/resources/add",
        ListView.as_view(),
        name="resource_set",
    ),
    path(
        "api/resource_set/<uuid:list_id>/resources/delete",
        ListView.as_view(),
        name="resource_set",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if (
    settings.APP_NAME != "Arches"
    and settings.APP_NAME not in settings.ARCHES_APPLICATIONS
):
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
