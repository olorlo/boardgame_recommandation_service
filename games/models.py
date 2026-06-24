from django.db import models
from django.conf import settings

class BoardGames(models.Model):
    game_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=200)
    rank = models.IntegerField()
    released_year = models.IntegerField()
    view_count = models.IntegerField(default=0)
    party_rank = models.IntegerField(null=True, blank=True)
    family_rank = models.IntegerField(null=True, blank=True)
    thumbnail_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    korean_title = models.CharField(max_length=200, blank=True)
    boardlife_rank = models.IntegerField(null=True, blank=True)
    boardlife_game_id = models.IntegerField(null=True, blank=True)
    boardlife_url = models.URLField(blank=True)

class GameDetails(models.Model):
    boardgame = models.ForeignKey(BoardGames, on_delete=models.CASCADE, related_name='details')
    min_players = models.IntegerField()
    max_players = models.IntegerField()
    playing_time = models.IntegerField()
    weight = models.FloatField()


class RecommendationFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendation_feedbacks')
    boardgame = models.ForeignKey(BoardGames, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendation_feedbacks')
    game_title = models.CharField(max_length=200)
    situation = models.TextField(blank=True)
    recommendation_reason = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    player_count = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
