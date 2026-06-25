import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from games.models import BoardGames

csv_path = 'boardlife_titles_1_40.csv'

updated_count = 0
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            if not row or not row.get('game_id'):
                continue
            game_id = int(row['game_id'])
            korean_title = row['korean_title']
            
            game = BoardGames.objects.filter(game_id=game_id).first()
            if game:
                game.korean_title = korean_title
                game.save(update_fields=['korean_title'])
                updated_count += 1
        except Exception as e:
            print(f"Error on {row.get('game_id')}: {e}")

print(f"Updated {updated_count} games.")
