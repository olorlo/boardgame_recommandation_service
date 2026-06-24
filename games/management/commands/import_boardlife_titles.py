import csv
import html
import re
import time
import unicodedata
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from games.models import BoardGames


BOARDLIFE_RANK_URL = "https://boardlife.co.kr/rank/all/{page}"
BOARDLIFE_ORIGIN = "https://boardlife.co.kr"


def normalize_title(value):
    value = html.unescape(str(value or "")).strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s:;&'+.-]", "", value)
    return value


def title_key(value):
    value = html.unescape(str(value or "")).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", value)


def strip_tags(value):
    return re.sub(r"<[^>]+>", "", value or "").strip()


def parse_rank_rows(page_html):
    blocks = re.findall(
        r"(<div id=\"check-list-\d+\" class='rank-row .*?)(?=<div id=\"check-list-\d+\" class='rank-row |\Z)",
        page_html,
        flags=re.DOTALL,
    )
    rows = []
    for block in blocks:
        game_id_match = re.search(r"id=\"check-list-(\d+)\"", block)
        rank_match = re.search(r"<div class=\"rank\"><div class=\"digits-\d+\">(\d+)</div></div>", block)
        title_match = re.search(
            r"<a href='(?P<href>/game/\d+)' class='title new-ellip'>\s*(?P<title>.*?)\s*</a>",
            block,
            flags=re.DOTALL,
        )
        english_match = re.search(
            r"<div class=\"bullet eng new-ellip\">(?P<title>.*?)</div>",
            block,
            flags=re.DOTALL,
        )
        year_match = re.search(
            r"<div class=\"bullet year new-ellip\">(?P<year>\d{4})",
            block,
            flags=re.DOTALL,
        )

        if not (game_id_match and rank_match and title_match and english_match):
            continue

        rows.append(
            {
                "boardlife_game_id": int(game_id_match.group(1)),
                "boardlife_rank": int(rank_match.group(1)),
                "boardlife_url": f"{BOARDLIFE_ORIGIN}{title_match.group('href')}",
                "korean_title": html.unescape(strip_tags(title_match.group("title"))),
                "english_title": html.unescape(strip_tags(english_match.group("title"))),
                "released_year": int(year_match.group("year")) if year_match else None,
            }
        )
    return rows


class Command(BaseCommand):
    help = "Import Korean titles from BoardLife rank pages and optionally write them to CSV."

    def add_arguments(self, parser):
        parser.add_argument("--start-page", type=int, default=1)
        parser.add_argument("--end-page", type=int, default=1)
        parser.add_argument(
            "--sleep",
            type=float,
            default=3.0,
            help="Seconds to wait between BoardLife requests.",
        )
        parser.add_argument("--timeout", type=float, default=15.0)
        parser.add_argument("--overwrite", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--csv-output",
            default="",
            help="Optional CSV path for matched BoardLife title rows.",
        )

    def handle(self, *args, **options):
        if options["start_page"] < 1 or options["end_page"] < options["start_page"]:
            raise ValueError("Use a valid page range, for example --start-page 1 --end-page 3.")

        matched_rows = []
        fetched = 0
        matched = 0
        updated = 0
        skipped = 0

        for page in range(options["start_page"], options["end_page"] + 1):
            rows = self.fetch_page(page, options["timeout"])
            fetched += len(rows)
            self.stdout.write(f"Page {page}: parsed {len(rows)} BoardLife row(s).")

            for row in rows:
                game = self.find_game(row)
                if game is None:
                    skipped += 1
                    continue

                matched += 1
                matched_rows.append(
                    {
                        "game_id": game.game_id,
                        "bgg_title": game.title,
                        **row,
                    }
                )

                if game.korean_title and not options["overwrite"]:
                    skipped += 1
                    continue

                if not options["dry_run"]:
                    game.korean_title = row["korean_title"]
                    game.boardlife_rank = row["boardlife_rank"]
                    game.boardlife_game_id = row["boardlife_game_id"]
                    game.boardlife_url = row["boardlife_url"]
                    game.save(
                        update_fields=[
                            "korean_title",
                            "boardlife_rank",
                            "boardlife_game_id",
                            "boardlife_url",
                        ]
                    )
                updated += 1

            if page < options["end_page"] and options["sleep"] > 0:
                time.sleep(options["sleep"])

        if options["csv_output"]:
            self.write_csv(options["csv_output"], matched_rows)

        label = "Would update" if options["dry_run"] else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{label} {updated} game(s). fetched={fetched}, matched={matched}, skipped={skipped}"
            )
        )

    def fetch_page(self, page, timeout):
        response = requests.get(
            BOARDLIFE_RANK_URL.format(page=page),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return parse_rank_rows(response.text)

    def find_game(self, row):
        normalized = normalize_title(row["english_title"])
        aggressive_key = title_key(row["english_title"])

        for game in BoardGames.objects.filter(title__iexact=row["english_title"])[:5]:
            if normalize_title(game.title) == normalized:
                return game

        key_matches = [
            game
            for game in BoardGames.objects.all()
            if title_key(game.title) == aggressive_key
        ]
        if len(key_matches) == 1:
            return key_matches[0]

        queryset = BoardGames.objects.all()
        if row["released_year"]:
            queryset = queryset.filter(released_year=row["released_year"])

        for game in queryset:
            if normalize_title(game.title) == normalized:
                return game
            if title_key(game.title) == aggressive_key:
                return game
        return None

    def write_csv(self, csv_output, rows):
        path = Path(csv_output)
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / path
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "game_id",
            "bgg_title",
            "korean_title",
            "english_title",
            "released_year",
            "boardlife_rank",
            "boardlife_game_id",
            "boardlife_url",
        ]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        self.stdout.write(f"Wrote CSV: {path}")
