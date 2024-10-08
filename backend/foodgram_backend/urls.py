from django.contrib import admin
from django.urls import include, path

from api.views import redirect_from_short_url


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<slug:short_url>/',
         redirect_from_short_url,
         name='redirect_from_short_url'),
]
