from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import ValidationError

from .models import Project, Tag, ToDo, Comment


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = Tag
        fields = ["id", "name", "project"]

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise ValidationError("Tag already exists")

    def create(self, validated_data):
        if self.context["request"].user not in validated_data["project"].members.all():
            raise serializers.ValidationError("Must be a member of the project!")
        return super().create(validated_data)


class ToDoSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )
    assignees = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = ToDo
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "tags",
            "assignees",
            "project",
            "order",
            "created_at",
            "updated_at",
        ]

    def extra_validation(self, project=None, tags=None, assignees=None, user=None):
        if tags and project:
            for tag in tags:
                if tag.project != project:
                    raise serializers.ValidationError(
                        "Can't set a tag that doesn't belong to the project!"
                    )
        if assignees and project:
            for assignee in assignees:
                if assignee not in project.members.all():
                    raise serializers.ValidationError(
                        "Can't assign someone who isn't a project member!"
                    )
        if user and user not in project.members.all():
            raise serializers.ValidationError("Must be a member of the project!")

    def update(self, instance, validated_data):
        tags = validated_data.get("tags")
        assignees = validated_data.get("assignees")
        project = instance.project
        self.extra_validation(project=project, tags=tags, assignees=assignees)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        print(validated_data)
        user = self.context["request"].user
        project = validated_data["project"]
        tags = validated_data["tags"]
        assignees = validated_data["assignees"]
        self.extra_validation(
            project=project, tags=tags, assignees=assignees, user=user
        )
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "todo", "author", "text", "created_at", "updated_at"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    todos = ToDoSerializer(many=True, read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "owner", "members", "todos", "tags"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "owner"]


class MemberSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
