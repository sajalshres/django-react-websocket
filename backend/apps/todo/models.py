from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="project_owned"
    )
    members = models.ManyToManyField(User, related_name="project_member")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        is_new = self.pk is None
        super().save(force_insert, force_update, using, update_fields)
        if is_new:
            self.members.add(self.owner)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=150)
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="tags"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "project"], name="project_name_unique"
            )
        ]

    def __str__(self):
        return self.name


class Priority(models.TextChoices):
    HIGH = "H", "High"
    MEDIUM = "M", "Medium"
    LOW = "L", "Low"


class ToDo(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=1, choices=Priority.choices, default=Priority.MEDIUM
    )
    tags = models.ManyToManyField(Tag, related_name="todos")
    assignees = models.ManyToManyField(User, related_name="todos")
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="todos"
    )
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.id} - {self.title}"


class Comment(models.Model):
    todo = models.ForeignKey(ToDo, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
