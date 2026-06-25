import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from games.models import BoardGames


def optional_int(value):
    try:
        number = int(float(value or 0))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


class Command(BaseCommand):
    help = "Import BoardLife Korean title matches from a previously generated CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="boardlife_titles_1_40.csv",
            help="CSV path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing Korean titles.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be updated without saving.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["path"])
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        updated = 0
        skipped = 0
        missing = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required_fields = {"game_id", "korean_title"}
            if not required_fields.issubset(set(reader.fieldnames or [])):
                raise CommandError(
                    "CSV must contain game_id and korean_title columns."
                )

            for row in reader:
                game_id = optional_int(row.get("game_id"))
                korean_title = str(row.get("korean_title") or "").strip()
                if not game_id or not korean_title:
                    skipped += 1
                    continue

                try:
                    game = BoardGames.objects.get(game_id=game_id)
                except BoardGames.DoesNotExist:
                    missing += 1
                    continue

                if game.korean_title and not options["overwrite"]:
                    skipped += 1
                    continue

                if not options["dry_run"]:
                    game.korean_title = korean_title
                    game.boardlife_rank = optional_int(row.get("boardlife_rank"))
                    game.boardlife_game_id = optional_int(row.get("boardlife_game_id"))
                    game.boardlife_url = str(row.get("boardlife_url") or "").strip()
                    game.save(
                        update_fields=[
                            "korean_title",
                            "boardlife_rank",
                            "boardlife_game_id",
                            "boardlife_url",
                        ]
                    )
                updated += 1

        label = "Would update" if options["dry_run"] else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{label} {updated} game(s). skipped={skipped}, missing_boardgames={missing}"
            )
        )
