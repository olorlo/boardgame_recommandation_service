import json
import os
import re
import requests
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import BoardGames, GameDetails, RecommendationFeedback
from .serializers import BoardGamesSerializer, GameDetailsSerializer
from django.conf import settings
from django.db.models import Q
from googleapiclient.discovery import build

RECOMMENDATION_BLOCKED_GAME_IDS = {521}
BOARDGAME_FALLBACK_IMAGE_URL = '/static/boardgame_fallback.png'


def _game_display_title(boardgame):
    return boardgame.korean_title or boardgame.title

# --- HTML & AJAX Views ---

def index(request):
    games = BoardGames.objects.all()[:50] # initial load limit
    context = {
        'games': games,
    }
    return render(request, 'games/index.html', context)

def filter_games(request):
    players = request.GET.get('players')
    time = request.GET.get('time')
    difficulty = request.GET.get('difficulty')
    
    details_qs = GameDetails.objects.all()
    
    if players:
        try:
            p = int(players)
            details_qs = details_qs.filter(min_players__lte=p, max_players__gte=p)
        except ValueError:
            pass
            
    if time:
        try:
            t = int(time)
            details_qs = details_qs.filter(playing_time__lte=t)
        except ValueError:
            pass
            
    if difficulty:
        if difficulty == 'easy':
            details_qs = details_qs.filter(weight__lte=2.0)
        elif difficulty == 'medium':
            details_qs = details_qs.filter(weight__gt=2.0, weight__lte=3.0)
        elif difficulty == 'hard':
            details_qs = details_qs.filter(weight__gt=3.0)

    boardgame_ids = details_qs.values_list('boardgame_id', flat=True)
    games = BoardGames.objects.filter(game_id__in=boardgame_ids).order_by('rank')[:50]
    
    data = []
    for g in games:
        data.append({
            'game_id': g.game_id,
            'title': g.title,
            'display_title': _game_display_title(g),
            'rank': g.rank,
            'released_year': g.released_year,
        })
        
    return JsonResponse({'games': data})


def _choice(value, default='상관없음'):
    value = str(value or '').strip()
    return value or default


def _parse_player_range(value):
    text = _choice(value, '')
    numbers = [int(number) for number in re.findall(r'\d+', text)]
    if not numbers:
        return None
    if '이상' in text:
        return numbers[0], numbers[0]
    if len(numbers) >= 2:
        return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
    return numbers[0], numbers[0]


def _parse_time_range(value):
    text = _choice(value, '')
    if not text:
        return None, None
    if '30' in text:
        return None, 30
    if '1시간' in text:
        return None, 75
    if '2시간' in text and '이상' in text:
        return 90, None

    numbers = [int(number) for number in re.findall(r'\d+', text)]
    if not numbers:
        return None, None
    if '이상' in text:
        return numbers[0], None
    return None, numbers[0]


def _difficulty_bounds(value, relaxed=False):
    text = _choice(value, '')
    if any(keyword in text for keyword in ['쉬움', '초보', '입문']):
        return None, 2.0 if relaxed else 1.8
    if '보통' in text:
        return 1.6 if relaxed else 1.8, 2.8 if relaxed else 2.6
    if any(keyword in text for keyword in ['어려움', '긱', '고수']):
        return 2.6 if relaxed else 2.8, None
    return None, None


def _apply_recommend_filters(queryset, player_range, time_range, difficulty_bounds):
    if player_range:
        min_players, max_players = player_range
        queryset = queryset.filter(min_players__lte=min_players, max_players__gte=max_players)

    min_time, max_time = time_range
    if min_time is not None:
        queryset = queryset.filter(playing_time__gte=min_time)
    if max_time is not None:
        queryset = queryset.filter(playing_time__lte=max_time)

    min_weight, max_weight = difficulty_bounds
    if min_weight is not None:
        queryset = queryset.filter(weight__gte=min_weight)
    if max_weight is not None:
        queryset = queryset.filter(weight__lte=max_weight)

    return queryset


def _rank_signal(value):
    return value if value and value > 0 else 999999


def _candidate_sort_key(detail, difficulty, preference):
    difficulty_text = _choice(difficulty, '')
    preference_text = _choice(preference, '')
    rank = detail.boardgame.rank or 999999
    weight = detail.weight if detail.weight is not None else 0
    party_rank = _rank_signal(detail.boardgame.party_rank)
    family_rank = _rank_signal(detail.boardgame.family_rank)

    if any(keyword in preference_text for keyword in ['파티', '시끌', '마피아', '블러핑']):
        return party_rank, family_rank, weight, rank

    if any(keyword in difficulty_text for keyword in ['쉬움', '초보', '입문']):
        return family_rank, party_rank, weight, rank

    if '보통' in difficulty_text:
        return abs(weight - 2.2), rank
    if any(keyword in difficulty_text for keyword in ['어려움', '긱', '고수']):
        return abs(weight - 3.2), rank
    return rank, weight


def _build_recommend_candidates(players, time, difficulty, preference, exclude_game_ids=None, limit=60, rank_limit=4000):
    base = (
        GameDetails.objects
        .select_related('boardgame')
        .filter(boardgame__rank__lte=rank_limit)
        .exclude(boardgame__korean_title='')
        .exclude(boardgame_id__in=RECOMMENDATION_BLOCKED_GAME_IDS)
        .order_by('boardgame__rank')
    )
    player_range = _parse_player_range(players)
    time_range = _parse_time_range(time)
    excluded_ids = set(exclude_game_ids or [])
    candidates_by_id = {}

    def add_candidates(queryset):
        for detail in sorted(queryset[:300], key=lambda item: _candidate_sort_key(item, difficulty, preference)):
            game_id = detail.boardgame.game_id
            if game_id in excluded_ids or game_id in candidates_by_id:
                continue
            candidates_by_id[game_id] = detail
            if len(candidates_by_id) >= limit:
                return True
        return False

    strict = _apply_recommend_filters(
        base,
        player_range,
        time_range,
        _difficulty_bounds(difficulty, relaxed=False),
    )
    if add_candidates(strict):
        return list(candidates_by_id.values())

    relaxed = _apply_recommend_filters(
        base,
        player_range,
        time_range,
        _difficulty_bounds(difficulty, relaxed=True),
    )
    if add_candidates(relaxed):
        return list(candidates_by_id.values())

    no_difficulty = _apply_recommend_filters(base, player_range, time_range, (None, None))
    if add_candidates(no_difficulty):
        return list(candidates_by_id.values())

    player_only = _apply_recommend_filters(base, player_range, (None, None), (None, None))
    if add_candidates(player_only):
        return list(candidates_by_id.values())

    add_candidates(base)
    return list(candidates_by_id.values())


def _extract_json_array(text):
    text = str(text or '').strip()
    match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
    if match:
        text = match.group(0)
    else:
        text = text.replace('```json', '').replace('```', '').strip()

    parsed = json.loads(text)
    if isinstance(parsed, dict):
        parsed = parsed.get('recommendations', [])
    if not isinstance(parsed, list):
        return []
    return parsed


def _fallback_reason(detail, difficulty):
    if any(keyword in _choice(difficulty, '') for keyword in ['쉬움', '초보', '입문']):
        return (
            f"{detail.min_players}~{detail.max_players}인 가능, {detail.playing_time}분, "
            f"긱 웨이트 {detail.weight:.1f}라 초보자에게 부담이 적은 편입니다."
        )
    return (
        f"{detail.min_players}~{detail.max_players}인 가능, {detail.playing_time}분, "
        f"긱 웨이트 {detail.weight:.1f}로 입력한 조건과 잘 맞습니다."
    )


def _cache_bgg_image(boardgame):
    if boardgame.thumbnail_url or boardgame.image_url:
        return boardgame.thumbnail_url or boardgame.image_url

    import xml.etree.ElementTree as ET

    token = getattr(settings, "BGG_TOKEN", "") or ""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(
            f"https://boardgamegeek.com/xmlapi2/thing?id={boardgame.game_id}",
            headers=headers,
            timeout=5,
        )
        if response.status_code == 202:
            return ""
        response.raise_for_status()

        root = ET.fromstring(response.content)
        item = root.find("item")
        if item is None:
            return ""

        thumbnail = item.findtext("thumbnail", default="").strip()
        image = item.findtext("image", default="").strip()
        if thumbnail or image:
            boardgame.thumbnail_url = thumbnail
            boardgame.image_url = image
            boardgame.save(update_fields=["thumbnail_url", "image_url"])
        return thumbnail or image
    except Exception as exc:
        print(f"BGG image cache error for {boardgame.title}: {exc}")
        return ""


def _recommendation_item(detail, reason):
    image_url = (
        detail.boardgame.thumbnail_url
        or detail.boardgame.image_url
        or _cache_bgg_image(detail.boardgame)
        or BOARDGAME_FALLBACK_IMAGE_URL
    )
    return {
        'game_id': detail.boardgame.game_id,
        'title': detail.boardgame.title,
        'display_title': _game_display_title(detail.boardgame),
        'reason': reason,
        'min_players': detail.min_players,
        'max_players': detail.max_players,
        'playing_time': detail.playing_time,
        'weight': detail.weight,
        'image_url': image_url,
    }


def _attach_recommendation_images(items):
    return items

def recommend_game(request, game_id):
    try:
        game = BoardGames.objects.get(game_id=game_id)
        
        # 1. Youtube API for video
        youtube_api_key = os.environ.get('YOUTUBE_API_KEY', '')
        video_id = None
        if youtube_api_key:
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            req = youtube.search().list(q=f"{game.title} 보드게임 룰 설명", part="snippet", type="video", maxResults=1)
            res = req.execute()
            if res['items']:
                video_id = res['items'][0]['id']['videoId']
        else:
            # Fallback dummy video for demonstration if no key
            video_id = "dQw4w9WgXcQ"
            
        gms_key = os.environ.get('GMS_KEY', '')
        gms_endpoint = os.environ.get('GMS_ENDPOINT', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
        summary = "AI 요약 기능을 사용할 수 없습니다. (API KEY 누락)"
        if gms_key:
            prompt = f"보드게임 '{game.title}'의 핵심 승리 조건과 턴 진행 방식을 3~4줄로 요약해줘."
            url = gms_endpoint
            payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {gms_key}"
            }
            
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=30)
                res.raise_for_status()
                data = res.json()
                summary = data['choices'][0]['message']['content'].strip()
            except Exception as e:
                summary = f"AI 호출 중 오류가 발생했습니다: {str(e)}"
                print("GMS API Error:", e)
            
        return JsonResponse({
            'youtube_videoId': video_id,
            'summary': summary
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def situation_recommend(request):
    try:
        data = request.data

        mbti = _choice(data.get('mbti'))
        players = _choice(data.get('players'))
        time = _choice(data.get('time'))
        difficulty = _choice(data.get('difficulty'))
        preference = _choice(data.get('preference'))
        theme = _choice(data.get('theme'))
        ai_comment = _choice(data.get('ai_comment'), '')
        exclude_game_ids = set()
        for raw_id in data.get('exclude_game_ids') or []:
            try:
                exclude_game_ids.add(int(raw_id))
            except (TypeError, ValueError):
                continue

        situation = f"MBTI: {mbti}, 인원수: {players}, 시간: {time}, 난이도: {difficulty}, 성향: {preference}, 테마: {theme}"
        if ai_comment:
            situation = f"{situation}, 추가 요청: {ai_comment[:500]}"

        candidates = _build_recommend_candidates(
            players,
            time,
            difficulty,
            preference,
            exclude_game_ids=exclude_game_ids,
        )
        if not candidates:
            return JsonResponse({
                'error': '새로 추천할 다른 후보가 부족합니다. 조건을 조금 완화해 주세요.'
            }, status=404)

        candidate_by_id = {detail.boardgame.game_id: detail for detail in candidates}
        candidate_lines = [
            (
                f"- game_id={detail.boardgame.game_id} | {_game_display_title(detail.boardgame)} ({detail.boardgame.title}) | "
                f"인원 {detail.min_players}~{detail.max_players}인 | "
                f"시간 {detail.playing_time}분 | 긱 웨이트 {detail.weight:.2f} | "
                f"BGG rank {detail.boardgame.rank} | "
                f"party rank {detail.boardgame.party_rank or '없음'} | "
                f"family rank {detail.boardgame.family_rank or '없음'}"
            )
            for detail in candidates
        ]
        game_list_str = "\n".join(candidate_lines)

        gms_key = os.environ.get('GMS_KEY', '')
        gms_endpoint = os.environ.get('GMS_ENDPOINT', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')

        ai_choices = []
        if gms_key:
            system_prompt = """당신은 보드게임 추천 큐레이터입니다.
제공된 후보 목록은 서버가 인원, 시간, 난이도로 이미 검증한 게임입니다.
반드시 후보 목록 안의 game_id만 골라야 합니다. 후보 밖 게임, 모르는 게임, 새 제목을 절대 만들지 마세요.
특히 초보자는 BoardGameGeek weight 2.0 초과를 어렵게 느낄 수 있으니, 쉬움/초보 조건에서는 더 낮은 weight를 우선하세요.
인사말이나 설명 문장 없이 JSON 배열만 출력하세요."""

            user_prompt = f"""[검증된 후보 목록]
{game_list_str}

[사용자 조건]
{situation}

후보 중 조건에 가장 잘 맞는 게임을 최대 3개까지 골라 주세요.
추천 이유에는 왜 인원/시간/난이도 조건에 맞는지와 사용자의 추가 요청을 어떻게 반영했는지 짧게 포함하세요.
포맷: [{{"game_id": 123, "reason": "..."}}]"""

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {gms_key}"
            }

            try:
                res = requests.post(gms_endpoint, json=payload, headers=headers, timeout=60)
                res.raise_for_status()
                ai_data = res.json()
                ai_choices = _extract_json_array(ai_data['choices'][0]['message']['content'])
            except Exception as e:
                print("GMS recommendation fallback:", e)

        result = []
        used_ids = set()
        title_to_candidate = {detail.boardgame.title.strip().lower(): detail for detail in candidates}
        title_to_candidate.update({
            detail.boardgame.korean_title.strip().lower(): detail
            for detail in candidates
            if detail.boardgame.korean_title
        })

        for item in ai_choices:
            raw_game_id = item.get('game_id') or item.get('id')
            detail = None
            try:
                detail = candidate_by_id.get(int(raw_game_id))
            except (TypeError, ValueError):
                title = str(item.get('title', '')).strip().lower()
                detail = title_to_candidate.get(title)

            if not detail or detail.boardgame.game_id in used_ids:
                continue

            reason = str(item.get('reason', '')).strip() or _fallback_reason(detail, difficulty)
            result.append(_recommendation_item(detail, reason[:500]))
            used_ids.add(detail.boardgame.game_id)
            if len(result) == 3:
                break

        for detail in candidates:
            if len(result) == 3:
                break
            if detail.boardgame.game_id in used_ids:
                continue
            result.append(_recommendation_item(detail, _fallback_reason(detail, difficulty)))
            used_ids.add(detail.boardgame.game_id)

        return JsonResponse({
            'recommendations': result,
            'candidate_count': len(candidates),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def recommendation_feedback(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    data = request.data
    game_title = str(data.get('game_title', '')).strip()
    if not game_title:
        return JsonResponse({'status': 'error', 'message': '게임 제목이 없습니다.'}, status=400)

    rating = data.get('rating')
    player_count = data.get('player_count')

    try:
        rating = int(rating) if rating not in [None, ''] else None
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': '별점은 숫자로 입력해주세요.'}, status=400)

    if rating is not None and not 1 <= rating <= 5:
        return JsonResponse({'status': 'error', 'message': '별점은 1~5점만 가능합니다.'}, status=400)

    try:
        player_count = int(player_count) if player_count not in [None, ''] else None
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': '인원수는 숫자로 입력해주세요.'}, status=400)

    boardgame = BoardGames.objects.filter(Q(title=game_title) | Q(korean_title=game_title)).first()
    feedback = RecommendationFeedback.objects.create(
        user=request.user,
        boardgame=boardgame,
        game_title=game_title,
        situation=str(data.get('situation', '')).strip(),
        recommendation_reason=str(data.get('recommendation_reason', '')).strip(),
        rating=rating,
        player_count=player_count,
        review=str(data.get('review', '')).strip(),
    )

    return JsonResponse({
        'status': 'success',
        'feedback_id': feedback.pk,
        'message': '리뷰가 저장되었습니다.',
    })


@api_view(['GET'])
def details_by_title(request):
    title = request.GET.get('title', '')
    if not title:
        return JsonResponse({'error': 'Title parameter is required.'}, status=400)
        
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY', '')
    video_id = None
    if youtube_api_key:
        try:
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            req = youtube.search().list(q=f"{title} 보드게임 룰 설명", part="snippet", type="video", maxResults=1)
            res = req.execute()
            if res['items']:
                video_id = res['items'][0]['id']['videoId']
        except Exception as e:
            print("Youtube Error:", e)
    else:
        video_id = "dQw4w9WgXcQ"
        
    details_data = None
    try:
        from .models import BoardGames, GameDetails
        game = BoardGames.objects.filter(Q(title=title) | Q(korean_title=title)).first()
        if game:
            game.view_count += 1
            game.save(update_fields=['view_count'])
            details = GameDetails.objects.filter(boardgame=game).first()
            if details:
                from .serializers import GameDetailsSerializer
                details_data = GameDetailsSerializer(details).data
    except Exception as e:
        print("Details Fetch Error:", e)
        
    gms_key = os.environ.get('GMS_KEY', '')
    gms_endpoint = os.environ.get('GMS_ENDPOINT', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
    summary = "AI 요약 기능을 사용할 수 없습니다. (API KEY 누락)"
    if gms_key:
        prompt = f"보드게임 '{title}'에 대해 초보자에게 승리 조건과 턴 진행 방식을 이모지를 섞어서 아주 짧게 2~3줄로 요약해줘."
        url = gms_endpoint
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gms_key}"
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            res.raise_for_status()
            data = res.json()
            summary = data['choices'][0]['message']['content'].strip()
        except Exception as e:
            summary = f"AI 호출 중 오류가 발생했습니다: {str(e)}"
            print("GMS Error:", e)
            
    return JsonResponse({
        'youtube_videoId': video_id,
        'ai_summary': summary,
        'details': details_data
    })

# --- Existing API Views ---

@api_view(['GET', 'POST'])
def boardgame_list(request):
    if request.method == 'GET':
        games = BoardGames.objects.all()
        serializer = BoardGamesSerializer(games, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        serializer = BoardGamesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "데이터 삽입 성공", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "데이터 삽입 실패", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def boardgame_detail(request, game_id):
    try:
        game = BoardGames.objects.get(game_id=game_id)
        game.view_count += 1
        game.save(update_fields=['view_count'])
        
        details = GameDetails.objects.filter(boardgame=game)
        if details.exists():
            serializer = GameDetailsSerializer(details.first())
            return Response(serializer.data)
        else:
            return Response({"message": "상세 정보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    except BoardGames.DoesNotExist:
        return Response({"message": "해당 게임을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def top_boardgame(request):
    try:
        top_game = BoardGames.objects.filter(rank__gt=0).order_by('rank').first()
        if top_game:
            details = GameDetails.objects.filter(boardgame=top_game).first()
            if details:
                serializer = GameDetailsSerializer(details)
                return Response(serializer.data)
            else:
                serializer = BoardGamesSerializer(top_game)
                return Response({"game": serializer.data, "message": "상세 정보가 없습니다."})
        return Response({"message": "게임을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def trending_boardgames(request):
    # view_count descending, then rank ascending
    games = BoardGames.objects.all().order_by('-view_count', 'rank')[:10]
    serializer = BoardGamesSerializer(games, many=True)
    return Response({'games': serializer.data})
