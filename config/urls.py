from django.contrib import admin
from django.urls import path, include
from django.conf import settings
import os

urlpatterns = [
    path("admin/", admin.site.urls),
]

api_prefix = "api/v1/"

apps_dir = os.path.join(settings.BASE_DIR, "apps")
for app in os.listdir(apps_dir):
    url_file = os.path.join(apps_dir, app, "urls.py")
    if os.path.isfile(url_file):
        if app == "impression":
            urlpatterns.append(path(f"{api_prefix}impressions/", include(f"apps.{app}.urls")))
        else:
            urlpatterns.append(path(f"{api_prefix}{app}/", include(f"apps.{app}.urls")))