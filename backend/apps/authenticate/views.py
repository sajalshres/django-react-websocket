from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .serializers import LoginSerializer, UserSerializer, RegisterSerializer


@api_view(["GET"])
def csrf_view(request):
    return Response({"csrftoken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def register_vew(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(**serializer.data)

    if user is None:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
        )

    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["GET"])
def logout_view(request):
    if not request.user.is_authenticated:
        return Response(
            {"detail": "You're not logged in."}, status=status.HTTP_400_BAD_REQUEST
        )

    logout(request)
    return Response({"detail": "Successfully logged out."})


class SessionView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return Response({"isAuthenticated": True})


class WhoAmIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return Response(UserSerializer(request.user))
