from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=User._meta.get_field("username").max_length,
        min_length=1,
        required=True,
    )
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("The two password fields didn't match.")
        return data

    def create(self, validated_data):
        validated_data["password"] = validated_data.pop("password1")
        del validated_data["password2"]
        return User.objects.create_user(**validated_data)
