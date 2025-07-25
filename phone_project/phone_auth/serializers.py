from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VerificationCode

User = get_user_model()


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)


class ActivateInviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):
    invited_users = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['phone_number', 'invite_code', 'activated_invite_code', 'invited_users']

    def get_invited_users(self, obj):
        users = User.objects.filter(activated_invite_code=obj.invite_code).exclude(id=obj.id)
        return [user.phone_number for user in users]
