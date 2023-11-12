# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('generate-story/', views.GenerateStoryView, name='generate_story'),
    path('current-user/', views.CurrentUserDetailView, name='current-user-detail'),
    path('search/', views.SearchAPIView, name='search-api'),
    path('update-profile/', views.update_profile, name='update-profile'),
    path('getStory/', views.get_story, name='Get_top_fifty'),
    path('getStory/<int:id>', views.get_story_by_id, name='Get_story_by_id')
]
