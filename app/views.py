from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.authtoken.models import Token
import json
from .models import User, Story
from .serializers import (
    UserRegistrationSerializer,
    UserSignInSerializer,
    PromptSerializer,
    StorySerializer,
)
from django.conf import settings
import google.generativeai as google_palm
from django.middleware.csrf import get_token
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from requests.exceptions import RequestException

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
                return Response(
                    {"token": token.key, "csrf": csrf_token}, status=status.HTTP_200_OK
                )
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


nlp = spacy.load("en_core_web_md")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def SearchAPIView(request):
    serializer = PromptSerializer(data=request.data)
    if serializer.is_valid():
        try:
            search_query = serializer.validated_data["prompt"]
            user_query_vec = nlp(search_query).vector
            prompts = Story.objects.values_list("prompt", flat=True)

            similarities = []

            for prompt in prompts:
                prompt_vec = nlp(prompt).vector
                similarity = cosine_similarity([user_query_vec], [prompt_vec])[0][0]
                similarities.append(similarity)

            threshold = 0.9
            print(similarities)
            similar_prompts = [
                prompt
                for prompt, similarity in zip(prompts, similarities)
                if similarity > threshold
            ]

            if similar_prompts:
                results = Story.objects.filter(prompt__in=similar_prompts)
                serializer = StorySerializer(results, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

            generated_story_response = generate_story(request, search_query)
            return generated_story_response

        except User.DoesNotExist:
            return Response(
                {"detail": "User is not logged in."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"detail": "An error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def GenerateStoryView(request):
    serializer = PromptSerializer(data=request.data)
    print(request.data)
    if serializer.is_valid():
        try:
            generated_story_response = generate_story(
                request, serializer.validated_data["prompt"]
            )
            return generated_story_response
        except User.DoesNotExist:
            return Response(
                {"detail": "User is not logged in."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def CurrentUserDetailView(request):
    try:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {"detail": "User is not logged in."}, status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {"detail": "An error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def generate_story(request, prompt_text, max_attempts=3):
    attempts = 0

    while attempts < max_attempts:
        try:
            google_palm.configure(api_key=settings.GOOGLE_API_KEY)
            prompt = "Craft an engaging narrative based on the ancient Indian epic, {prompt_text}. Create the story in well structured JSON format, including a title, story, and book_reference. The story should be extensive, spanning over 900 words, and organized into three well-structured paragraphs. Explore themes such as Good habits, discipline life, and various other life lessons. Feel free to incorporate specific details and emotions to bring the story to life."
            defaults = {
                "model": "models/text-bison-001",
                "temperature": 0.7,
                "candidate_count": 1,
                "top_k": 40,
                "top_p": 0.95,
                "max_output_tokens": 2048,
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
            data = json.loads(response.result[7:-3].replace("\n", " "))
            new_story = Story(prompt=prompt_text, title=data['title'], story=data["story"], reference_book=data["book_reference"], user=request.user)
            new_story.publish()
            request.user.stories.add(new_story)
            return Response(
                {
                    "story": data["story"],
                    "title": data["title"],
                    "book_reference": data["book_reference"],
                },
                status=status.HTTP_200_OK,
            )

        except (RequestException, Exception) as e:
            attempts += 1

    return Response({"error": f"Failed after {max_attempts} attempts. Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_story(request):
    story = Story.objects.order_by('-creation_date')[:50]
    serializer = StorySerializer(story, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_story_by_id(request, id):
    try:
        story = Story.objects.get(id=id)
    except Story.DoesNotExist:
        return Response({"message": "Story does not exist"}, status=status.HTTP_404_NOT_FOUND)

    try:
        serializer = StorySerializer(story)
    except Exception as e:
        return Response({"message": "Error occurred during serialization", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        request.user.last_reading = story
        request.user.save()
    except Exception as e:
        return Response({"message": "Error occurred while updating user's last reading", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_last_reading(request):
    user = request.user
    last_reading = user.last_reading
    if last_reading:
        serializer = StorySerializer(last_reading)
        return Response(serializer.data, status= status.HTTP_200_OK)
    else:
        return Response("User has no last reading", status=status.HTTP_404_NOT_FOUND)
