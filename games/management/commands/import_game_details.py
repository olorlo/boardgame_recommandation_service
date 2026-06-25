import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from games.models import BoardGames, GameDetails


def optional_text(value):
    return str(value or "").strip()


def required_int(value, field_name):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer.")


def required_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")


class Command(BaseCommand):
    help = "Import board game detail stats from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/game_details.csv",
            help="CSV path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        csv_path = Path(options["path"])
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        imported = 0
        skipped = 0
        missing = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required_fields = {
                "game_id",
                "min_players",
                "max_players",
                "playing_time",
                "weight",
            }
            if not required_fields.issubset(set(reader.fieldnames or [])):
                raise CommandError(
                    "CSV must contain game_id, min_players, max_players, playing_time, and weight columns."
                )

            for row in reader:
                try:
                    game_id = required_int(row.get("game_id"), "game_id")
                    min_players = required_int(row.get("min_players"), "min_players")
                    max_players = required_int(row.get("max_players"), "max_players")
                    playing_time = required_int(row.get("playing_time"), "playing_time")
                    weight = required_float(row.get("weight"), "weight")
                except ValueError:
                    skipped += 1
                    continue

                try:
                    game = BoardGames.objects.get(game_id=game_id)
                except BoardGames.DoesNotExist:
                    missing += 1
                    continue

                if not options["dry_run"]:
                    GameDetails.objects.update_or_create(
                        boardgame=game,
                        defaults={
                            "min_players": min_players,
                            "max_players": max(max_players, min_players),
                            "playing_time": playing_time,
                            "weight": weight,
                        },
                    )

                    update_fields = []
                    title = optional_text(row.get("title"))
                    korean_title = optional_text(row.get("korean_title"))
                    rank = row.get("rank")
                    thumbnail_url = optional_text(row.get("thumbnail_url"))
                    image_url = optional_text(row.get("image_url"))
                    if title and game.title != title:
                        game.title = title
                        update_fields.append("title")
                    if korean_title and game.korean_title != korean_title:
                        game.korean_title = korean_title
                        update_fields.append("korean_title")
                    if rank not in [None, ""]:
                        try:
                            parsed_rank = required_int(rank, "rank")
                        except ValueError:
                            parsed_rank = None
                        if parsed_rank and game.rank != parsed_rank:
                            game.rank = parsed_rank
                            update_fields.append("rank")
                    if thumbnail_url and game.thumbnail_url != thumbnail_url:
                        game.thumbnail_url = thumbnail_url
                        update_fields.append("thumbnail_url")
                    if image_url and game.image_url != image_url:
                        game.image_url = image_url
                        update_fields.append("image_url")
                    if update_fields:
                        game.save(update_fields=update_fields)
                imported += 1

        label = "Would import" if options["dry_run"] else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{label} {imported} detail row(s). skipped={skipped}, missing_boardgames={missing}"
            )
        )
