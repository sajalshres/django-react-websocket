from django.urls import path, include
from rest_framework import routers

from .views import (
    ProjectViewSet,
    TagViewSet,
    ToDoViewSet,
    CommentViewSet,
    SortToDoAPIView,
)

router = routers.DefaultRouter()
router.register(r"projects", ProjectViewSet)
router.register(r"tags", TagViewSet)
router.register(r"todos", ToDoViewSet)
router.register(r"comments", CommentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sort-todos/", SortToDoAPIView.as_view(), name="sort-todo"),
]
