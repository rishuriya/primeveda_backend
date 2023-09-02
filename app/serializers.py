# serializers.py

from rest_framework import serializers
from .models import User as abstrctUser
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = abstrctUser
        fields = ['username', 'password', 'email']

class UserSignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=500)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']