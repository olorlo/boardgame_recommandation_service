import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from games.models import RuleSummary


class Command(BaseCommand):
    help = "Export fixed rule summaries to a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/rule_summaries.json",
            help="JSON path relative to BASE_DIR, or an absolute path.",
        )
        parser.add_argument(
            "--verified-only",
            action="store_true",
            help="Export only summaries marked as verified.",
        )

    def handle(self, *args, **options):
        queryset = RuleSummary.objects.select_related("boardgame").order_by("boardgame__rank")
        if options["verified_only"]:
            queryset = queryset.filter(is_verified=True)

        rows = [
            {
                "game_id": item.boardgame_id,
                "title": item.boardgame.title,
                "korean_title": item.boardgame.korean_title,
                "summary": item.summary,
                "source": item.source,
                "source_url": item.source_url,
                "model_name": item.model_name,
                "is_verified": item.is_verified,
            }
            for item in queryset
        ]

        json_path = Path(options["path"])
        if not json_path.is_absolute():
            json_path = Path(settings.BASE_DIR) / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"Exported {len(rows)} rule summarie(s) to {json_path}"))
