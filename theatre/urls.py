from django.urls import include, path
from rest_framework import routers

from theatre.views import TheatreHallViewSet

app_name = "theatre"

router = routers.DefaultRouter()
router.register("theatre_halls", TheatreHallViewSet)

urlpatterns = [path("", include(router.urls))]
