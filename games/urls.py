from django.urls import path
from . import views

app_name = 'games'
urlpatterns = [
    # API routes
    path('api/', views.boardgame_list, name='api_boardgame_list'),
    path('api/<int:game_id>/details/', views.boardgame_detail, name='api_boardgame_detail'),
    path('api/details_by_title/', views.details_by_title, name='api_details_by_title'),
    path('api/top/', views.top_boardgame, name='api_top_boardgame'),
    path('api/recommendation-feedback/', views.recommendation_feedback, name='api_recommendation_feedback'),
    path('api/recommendation-reviews/', views.recommendation_reviews, name='api_recommendation_reviews'),
    path('api/trending/', views.trending_boardgames, name='api_trending_boardgames'),
    
    # HTML & AJAX routes
    path('', views.index, name='index'),
    path('filter/', views.filter_games, name='filter_games'),
    path('recommend/', views.situation_recommend, name='situation_recommend'),
    path('<int:game_id>/recommend/', views.recommend_game, name='recommend_game'),
]
