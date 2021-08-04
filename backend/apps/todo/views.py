from itertools import chain

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import mixins
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend

from utils import action, sort_model
from .models import Project, Tag, ToDo, Comment
from .serializers import (
    ProjectMemberSerializer,
    ProjectDetailSerializer,
    ProjectSerializer,
    TagSerializer,
    ToDoSerializer,
    CommentSerializer,
    MemberSerializer,
)
from .permissions import IsOwnerForDangerousMethods

User = get_user_model()


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerForDangerousMethods]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        queryset_by_user = super().get_queryset().filter(members=user)
        assignees = self.request.query_params.get("assignees", None)
        if self.action == "retrieve":
            retrieve_queryset = None
            if assignees:
                retrieve_queryset = (
                    ToDo.objects.filter(
                        Q(assignees__in=[int(x) for x in assignees.split(",")])
                    )
                    .order_by("id")
                    .distinct("id")
                )
            return queryset_by_user.prefetch_related(
                Prefetch("todos", queryset=retrieve_queryset)
            )
        return queryset_by_user

    def get_member(self):
        try:
            member = User.objects.get(username=self.request.data.get("username"))
        except User.DoesNotExist:
            return None

        return member

    @action(
        detail=True,
        methods=["post"],
        serializer_class=MemberSerializer,
        permission_classes=[IsAuthenticated],
    )
    def invite_member(self, request, pk):
        users_ids = self.request.data.get("users")
        if not users_ids:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        new_members = User.objects.filter(id__in=users_ids)
        if len(new_members) != len(users_ids):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.get_object().members.add(*new_members)
        return Response(ProjectMemberSerializer(instance=new_members, many=True).data)

    @action(detail=True, methods=["post"], serializer_class=MemberSerializer)
    def remove_member(self, request, pk):
        member = self.get_member()
        project = self.get_object()

        if (
            not member
            or member == project.owner
            or project not in member.projects.all()
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        project.members.remove(member)
        for todo in ToDo.objects.filter(project=project):
            todo.assignees.remove(member)
        return Response(data=ProjectMemberSerializer(instance=member).data)


class TagViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(project__members=self.request.user)


class ToDoViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = ToDo.objects.all()
    serializer_class = ToDoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(project__members=self.request.user)


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["todo"]

    def get_queryset(self):
        return super().get_queryset().filter(todo__project__members=self.request.user)

    def create(self, request, *args, **kwargs):
        request.data.update(dict(author=request.user.id))

        if (
            self.request.user
            not in ToDo.objects.get(id=request.data.get("todo")).project.members.all()
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        request.data.update(dict(author=request.user.id))

        if self.request.user != self.get_object().author:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)


class SortToDoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, **kwargs):
        print(request.data)
        try:
            return Response(
                status=sort_model(ToDo, ordered_ids=request.data.get("order", []))
            )
        except (
            KeyError,
            IndexError,
            AttributeError,
            ValueError,
            ToDo.DoesNotExist,
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
