import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from games.models import BoardGames, RuleSummary


class Command(BaseCommand):
    help = "Import fixed rule summaries from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/rule_summaries.json",
            help="JSON path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        json_path = Path(options["path"])
        if not json_path.is_absolute():
            json_path = Path(settings.BASE_DIR) / json_path
        if not json_path.exists():
            raise CommandError(f"JSON file not found: {json_path}")

        rows = json.loads(json_path.read_text(encoding="utf-8-sig"))
        if not isinstance(rows, list):
            raise CommandError("Rule summary JSON must be a list of objects.")

        updated = 0
        skipped = 0
        missing = 0
        for row in rows:
            game_id = row.get("game_id")
            summary = str(row.get("summary") or "").strip()
            if not game_id or not summary:
                skipped += 1
                continue

            try:
                boardgame = BoardGames.objects.get(game_id=int(game_id))
            except (BoardGames.DoesNotExist, TypeError, ValueError):
                missing += 1
                continue

            if not options["dry_run"]:
                RuleSummary.objects.update_or_create(
                    boardgame=boardgame,
                    defaults={
                        "summary": summary,
                        "source": str(row.get("source") or "imported").strip(),
                        "source_url": str(row.get("source_url") or "").strip(),
                        "model_name": str(row.get("model_name") or "").strip(),
                        "is_verified": bool(row.get("is_verified", False)),
                    },
                )
            updated += 1

        label = "Would import" if options["dry_run"] else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{label} {updated} rule summarie(s). skipped={skipped}, missing_boardgames={missing}"
            )
        )
