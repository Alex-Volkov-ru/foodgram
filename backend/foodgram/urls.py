from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from api.views import recipe_redirect

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('s/<str:short_hash>/', recipe_redirect, name='recipe-short-link'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
