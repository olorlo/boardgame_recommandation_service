import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from games.models import BoardGames


def optional_rank(value):
    try:
        rank = int(float(value or 0))
    except (TypeError, ValueError):
        return None
    return rank if rank > 0 else None


class Command(BaseCommand):
    help = "Import ranked board games from the BGG CSV export."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="boardgames_ranks.csv",
            help="CSV path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=3000,
            help="Highest BGG rank to import.",
        )
        parser.add_argument(
            "--include-expansions",
            action="store_true",
            help="Include rows marked as expansions.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["path"])
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        imported = 0
        skipped = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                try:
                    rank = int(float(row.get("rank") or 0))
                    game_id = int(float(row.get("id") or 0))
                    released_year = int(float(row.get("yearpublished") or 0))
                except (TypeError, ValueError):
                    skipped += 1
                    continue

                if rank <= 0 or rank > options["limit"]:
                    skipped += 1
                    continue
                if not options["include_expansions"] and str(row.get("is_expansion") or "0") == "1":
                    skipped += 1
                    continue

                title = str(row.get("name") or "").strip()
                if not title:
                    skipped += 1
                    continue

                BoardGames.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        "title": title,
                        "rank": rank,
                        "released_year": released_year,
                        "party_rank": optional_rank(row.get("partygames_rank")),
                        "family_rank": optional_rank(row.get("familygames_rank")),
                    },
                )
                imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported/updated {imported} game(s) up to rank {options['limit']}. skipped={skipped}"
            )
        )
