# urls.py

from django.urls import path
from . import views
from django.conf.urls.static import static
from primeveda_backend import settings
urlpatterns = [
    path('register/', views.register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('generate-story/', views.GenerateStoryView, name='generate_story'),
    path('current-user/', views.CurrentUserDetailView, name='current-user-detail'),
    path('search/', views.SearchAPIView, name='search-api'),
    path('update-profile/', views.update_profile, name='update-profile'),
    path('getStory/', views.get_story, name='Get_top_fifty'),
    path('getStory/<int:id>/', views.get_story_by_id, name='Get_story_by_id'),
    path('user/last_reading/', views.get_last_reading, name='Get_user_last_story'),
    path('user/add_favorite/<int:id>', views.add_favorite, name='Add_user_favorite_story'),
    path('user/favorite/', views.get_favorite, name='Get_user_favorite_story'),
    path('user/collection/', views.get_collection, name='Get_user_collection_story'),
    path('health_check/', views.health_check, name='health_check'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)