from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ingestions', views.RawIngestionViewSet, basename='ingestion')

urlpatterns = [
    path('ingestions/upload/', views.upload_file, name='upload-file'),
    path('', include(router.urls)),
]
