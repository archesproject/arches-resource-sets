from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

from arches_resource_sets.views.resource_set_view import (
    ResourceSetView,
)
from arches_resource_sets.views.resource_set_member_view import (
    ResourceSetMemberView,
)
from arches_resource_sets.views.resource_set_members_bulk_view import (
    ResourceSetMembersBulkView,
)

urlpatterns = [
    path("resource_sets/", ResourceSetView.as_view(), name="resource_sets"),
    path(
        "resource_sets/<uuid:set_id>",
        ResourceSetView.as_view(),
        name="resource_set",
    ),
    path(
        "resource_sets/<uuid:set_id>/members/",
        ResourceSetMemberView.as_view(),
        name="resource_set_members",
    ),
    path(
        "resource_sets/<uuid:set_id>/members/<uuid:resource_id>",
        ResourceSetMemberView.as_view(),
        name="resource_set_member",
    ),
    path(
        "resource_sets/<uuid:set_id>/bulk",
        ResourceSetMembersBulkView.as_view(),
        name="resource_set_members_bulk",
    ),
]
# Ensure Arches core urls are superseded by project-level urls
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if settings.ROOT_URLCONF == __name__:
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
