from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('me/', views.current_user, name='current_user'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('settings/', views.account_settings, name='account_settings'),
    path('<int:user_pk>/profile/', views.profile, name='profile'),
    path('<int:user_pk>/follow/', views.follow, name='follow'),
    path('profile/upload-image/', views.upload_profile_image, name='upload_profile_image'),
]
