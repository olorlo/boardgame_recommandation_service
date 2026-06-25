import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from games.models import GameDetails


class Command(BaseCommand):
    help = "Export board game detail stats to a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/game_details.csv",
            help="CSV path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument(
            "--rank-max",
            type=int,
            default=3000,
            help="Only export games at or above this BGG rank.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["path"])
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        queryset = (
            GameDetails.objects
            .select_related("boardgame")
            .filter(boardgame__rank__gt=0, boardgame__rank__lte=options["rank_max"])
            .order_by("boardgame__rank")
        )

        fieldnames = [
            "game_id",
            "title",
            "korean_title",
            "rank",
            "min_players",
            "max_players",
            "playing_time",
            "weight",
            "thumbnail_url",
            "image_url",
        ]
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for detail in queryset:
                game = detail.boardgame
                writer.writerow({
                    "game_id": game.game_id,
                    "title": game.title,
                    "korean_title": game.korean_title,
                    "rank": game.rank,
                    "min_players": detail.min_players,
                    "max_players": detail.max_players,
                    "playing_time": detail.playing_time,
                    "weight": detail.weight,
                    "thumbnail_url": game.thumbnail_url,
                    "image_url": game.image_url,
                })

        self.stdout.write(self.style.SUCCESS(f"Exported {queryset.count()} detail row(s) to {csv_path}"))
