import time
import xml.etree.ElementTree as ET

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from games.models import BoardGames, GameDetails


class Command(BaseCommand):
    help = "Fetch missing BoardGameGeek detail stats for BoardGames."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of games to fetch. Use --all for every missing game.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Fetch all missing details.",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Refresh games that already have details.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=1.5,
            help="Seconds to wait between BGG requests.",
        )
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Retries when BGG returns a queued/temporary response.",
        )
        parser.add_argument(
            "--rank-max",
            type=int,
            default=3000,
            help="Only fetch games at or above this BGG rank.",
        )
        parser.add_argument(
            "--category",
            choices=["all", "party", "family"],
            default="all",
            help="Prioritize/fetch games with a category rank.",
        )
        parser.add_argument(
            "--korean-only",
            action="store_true",
            help="Only fetch games that already have a Korean title.",
        )

    def handle(self, *args, **options):
        queryset = BoardGames.objects.filter(rank__gt=0, rank__lte=options["rank_max"]).order_by("rank")
        if options["korean_only"]:
            queryset = queryset.exclude(korean_title="")
        if options["category"] == "party":
            queryset = queryset.filter(party_rank__isnull=False).order_by("party_rank", "rank")
        elif options["category"] == "family":
            queryset = queryset.filter(family_rank__isnull=False).order_by("family_rank", "rank")
        if not options["refresh"]:
            queryset = queryset.exclude(details__isnull=False)
        if not options["all"]:
            queryset = queryset[: options["limit"]]

        total = queryset.count() if hasattr(queryset, "count") else len(queryset)
        created = 0
        skipped = 0
        failed = 0

        self.stdout.write(f"Fetching BGG details for {total} game(s).")

        for index, game in enumerate(queryset, start=1):
            try:
                payload = self.fetch_bgg_item(game.game_id, options["max_retries"], options["sleep"])
                if not payload:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"[{index}/{total}] skipped {game.title}"))
                    continue

                GameDetails.objects.update_or_create(
                    boardgame=game,
                    defaults={
                        "min_players": payload["min_players"],
                        "max_players": payload["max_players"],
                        "playing_time": payload["playing_time"],
                        "weight": payload["weight"],
                    },
                )
                game.thumbnail_url = payload["thumbnail_url"]
                game.image_url = payload["image_url"]
                game.save(update_fields=["thumbnail_url", "image_url"])
                created += 1
                self.stdout.write(self.safe_text(
                    f"[{index}/{total}] {game.title}: "
                    f"{payload['min_players']}~{payload['max_players']}p, "
                    f"{payload['playing_time']}m, weight {payload['weight']:.2f}, "
                    f"image={'yes' if payload['thumbnail_url'] or payload['image_url'] else 'no'}"
                ))
            except Exception as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(self.safe_text(f"[{index}/{total}] failed {game.title}: {exc}")))

            if index < total and options["sleep"] > 0:
                time.sleep(options["sleep"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. saved={created}, skipped={skipped}, failed={failed}, total={total}"
            )
        )

    def fetch_bgg_item(self, game_id, max_retries, sleep_seconds):
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
        last_response = None
        token = getattr(settings, "BGG_TOKEN", "") or ""
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        for attempt in range(max_retries + 1):
            response = requests.get(url, headers=headers, timeout=15)
            last_response = response

            if response.status_code == 401 and headers:
                self.stdout.write(
                    self.style.WARNING("BGG token was rejected. Retrying without Authorization header.")
                )
                headers = {}
                continue
            if response.status_code == 202:
                time.sleep(max(2, sleep_seconds))
                continue
            if response.status_code == 429 and attempt < max_retries:
                retry_after = response.headers.get("Retry-After")
                try:
                    wait_seconds = float(retry_after)
                except (TypeError, ValueError):
                    wait_seconds = max(10, sleep_seconds * 4)
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()

            root = ET.fromstring(response.content)
            item = root.find("item")
            if item is not None:
                return self.parse_item(item)

            if attempt < max_retries:
                time.sleep(max(2, sleep_seconds))

        if last_response is not None:
            last_response.raise_for_status()
        return None

    def safe_text(self, value):
        output = getattr(self.stdout, "_out", None)
        encoding = getattr(output, "encoding", None) or "utf-8"
        return str(value).encode(encoding, errors="replace").decode(encoding)

    def parse_item(self, item):
        min_players = self.int_value(item.find("minplayers"), default=1)
        max_players = self.int_value(item.find("maxplayers"), default=min_players)
        playing_time = self.int_value(item.find("playingtime"), default=0)
        weight = self.float_value(item.find("./statistics/ratings/averageweight"), default=0.0)
        thumbnail_url = self.text_value(item.find("thumbnail"))
        image_url = self.text_value(item.find("image"))

        return {
            "min_players": min_players,
            "max_players": max(max_players, min_players),
            "playing_time": playing_time,
            "weight": weight,
            "thumbnail_url": thumbnail_url,
            "image_url": image_url,
        }

    def int_value(self, element, default=0):
        if element is None:
            return default
        try:
            return int(float(element.attrib.get("value", default)))
        except (TypeError, ValueError):
            return default

    def float_value(self, element, default=0.0):
        if element is None:
            return default
        try:
            return float(element.attrib.get("value", default))
        except (TypeError, ValueError):
            return default

    def text_value(self, element):
        if element is None or element.text is None:
            return ""
        return element.text.strip()
