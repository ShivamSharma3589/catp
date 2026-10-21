from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'picture', 'is_staff', 'date_joined')
        read_only_fields = fields


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(write_only=True, trim_whitespace=True)
