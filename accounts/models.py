from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    followings = models.ManyToManyField('self', symmetrical=False, related_name='followers')
    profile_image = models.FileField(upload_to='profiles/', blank=True)
    favorite_games = models.ManyToManyField('games.BoardGames', blank=True, related_name='fans')
    favorite_game_tags = models.TextField(blank=True)

    @property
    def favorite_game_tag_list(self):
        return [tag for tag in self.favorite_game_tags.split(',') if tag]
