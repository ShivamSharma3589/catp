from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import GoogleLoginSerializer, UserSerializer
from .services import get_or_create_user, verify_google_credential


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class GoogleLoginView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        claims = verify_google_credential(serializer.validated_data['credential'])
        user, created = get_or_create_user(claims)

        return Response(
            {
                'user': UserSerializer(user).data,
                'tokens': issue_tokens(user),
                'created': created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        token = request.data.get('refresh')
        if not token:
            return Response(
                {'detail': 'A refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response(
                {'detail': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class DevTokenView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not (settings.DEBUG and settings.ALLOW_DEV_TOKEN):
            raise Http404()

        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response(
                {'detail': 'An email address is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'full_name': request.data.get('full_name') or email.split('@')[0]},
        )
        return Response(
            {'user': UserSerializer(user).data, 'tokens': issue_tokens(user), 'created': created},
            status=status.HTTP_200_OK,
        )
