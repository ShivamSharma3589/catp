from django.conf import settings
from django.db import transaction
from django.utils import timezone
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework.exceptions import PermissionDenied

from .exceptions import GoogleAuthUnavailable, InvalidGoogleCredential


def verify_google_credential(credential):
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        raise GoogleAuthUnavailable()

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=settings.GOOGLE_AUTH_CLOCK_SKEW_SECONDS,
        )
    except (ValueError, GoogleAuthError) as exc:
        raise InvalidGoogleCredential(f'Invalid Google credential: {exc}') from exc

    if not claims.get('email'):
        raise InvalidGoogleCredential('Google credential has no email address.')
    if not claims.get('email_verified'):
        raise InvalidGoogleCredential('Google email address is not verified.')
    if not claims.get('sub'):
        raise InvalidGoogleCredential('Google credential has no subject identifier.')

    return claims


@transaction.atomic
def get_or_create_user(claims):
    from .models import User

    sub = claims['sub']
    email = User.objects.normalize_email(claims['email'])
    full_name = claims.get('name', '') or ''
    picture = claims.get('picture', '') or ''

    user = User.objects.filter(google_sub=sub).first()
    created = False

    if user is None:
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                google_sub=sub,
                full_name=full_name,
                picture=picture,
            )
            created = True
        else:
            user.google_sub = sub

    if not user.is_active:
        raise PermissionDenied('This account has been disabled.')

    user.email = email
    user.full_name = full_name or user.full_name
    user.picture = picture or user.picture
    now = timezone.now()
    user.last_login_at = now
    user.last_login = now
    user.save(update_fields=[
        'email', 'google_sub', 'full_name', 'picture', 'last_login_at', 'last_login',
    ])

    return user, created
