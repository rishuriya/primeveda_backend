from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import (
    User,
    Story
)
from .serializers import (
    UserRegistrationSerializer,
    UserSignInSerializer,
    PromptSerializer,
)
from django.conf import settings
import google.generativeai as google_palm
from django.middleware.csrf import get_token
from .serializers import UserSerializer
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.is_active = False 
        user.save()


        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = reverse(
            "activate_account", kwargs={"uidb64": uid, "token": token}
        )
        activation_url = f"http://{get_current_site(request).domain}{activation_link}"

        subject = "Activate Your Account"
        message = f"Hello {user.username},\n\nPlease click the link below to activate your account:\n\n{activation_url}\n\nIf you didn't request this activation, please ignore this email."
        from_email = settings.EMAIL_HOST_USER 
        recipient_list = [user.email]

        send_mail(subject, message, from_email, recipient_list)

        return Response(
            {
                "message": "User registered successfully. Check your email for activation instructions."
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return Response(
            {"message": "Account activated successfully."}, status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"error": "Activation link is invalid or expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    serializer = UserSignInSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                token, _ = Token.objects.get_or_create(user=user)
                csrf_token = get_token(request)
                return Response({"token": token.key,"csrf":csrf_token}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Account is not activated."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@login_required(login_url='sign-in/')
def GenerateStoryView(request):
    serializer = PromptSerializer(data=request.data)
    print(request.data)
    if serializer.is_valid():
        prompt = "generate a story based on indian ancient text on context "+serializer.validated_data["prompt"]
        try:
            google_palm.configure(api_key=settings.GOOGLE_API_KEY)

            defaults = {
                "model": "models/text-bison-001",
                "temperature": 0.7,
                "candidate_count": 1,
                "top_k": 40,
                "top_p": 0.95,
                "max_output_tokens": 1024,
                "stop_sequences": [],
                "safety_settings": [
                    {"category": "HARM_CATEGORY_DEROGATORY", "threshold": 1},
                    {"category": "HARM_CATEGORY_TOXICITY", "threshold": 1},
                    {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 2},
                    {"category": "HARM_CATEGORY_SEXUAL", "threshold": 2},
                    {"category": "HARM_CATEGORY_MEDICAL", "threshold": 2},
                    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": 2},
                ],
            }

            response = google_palm.generate_text(**defaults, prompt=prompt)
            generated_story = response.result
            title_prompt="Generate title of the give story \n"+generated_story
            title=google_palm.generate_text(**defaults, prompt=title_prompt)

            new_story = Story(prompt=serializer.validated_data["prompt"], title=title.result, story=generated_story)
            new_story.publish()
            return Response({"story": generated_story,"title":title.result}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@login_required(login_url='sign-in/')
def CurrentUserDetailView(request):
    serializer=UserSerializer(request.user)
    print(serializer.data)
    return Response(serializer.data)