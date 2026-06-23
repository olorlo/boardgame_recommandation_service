import json
import os
import requests
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import BoardGames, GameDetails
from .serializers import BoardGamesSerializer, GameDetailsSerializer
from django.conf import settings
from googleapiclient.discovery import build

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
            'rank': g.rank,
            'released_year': g.released_year,
        })
        
    return JsonResponse({'games': data})

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
        situation = data.get('situation', '')
        
        gms_key = os.environ.get('GMS_KEY', '')
        gms_endpoint = os.environ.get('GMS_ENDPOINT', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
        if not gms_key:
            return JsonResponse({'error': 'GMS_KEY is not set.'}, status=500)
            
        import random
        # DB에 있는 게임 목록 가져오기: RAG 다양성을 위해 상위 1000개 중 랜덤 150개 추출 (스펙 포함)
        all_ids = list(GameDetails.objects.filter(boardgame__rank__lte=1000).values_list('id', flat=True))
        if all_ids:
            selected_ids = random.sample(all_ids, min(150, len(all_ids)))
            details = GameDetails.objects.filter(id__in=selected_ids).select_related('boardgame')
        else:
            details = []
            
        game_list_lines = []
        for d in details:
            game_list_lines.append(f"- {d.boardgame.title} (인원: {d.min_players}~{d.max_players}인, 시간: {d.playing_time}분, 난이도: {d.weight}/5.0)")
            
        game_list_str = "\n".join(game_list_lines) if game_list_lines else "(현재 DB에 게임 정보가 없습니다)"
        
        system_prompt = """당신은 방구석에서 10년 동안 보드게임만 연구한, 통찰력 있는 B급 감성의 보드게임 오타쿠 전문가입니다.
사용자가 입력한 상황(인원수, 시간 등)과 제공된 [데이터베이스 목록]의 게임 스펙(인원, 시간, 난이도)을 꼼꼼히 대조하여, 조건에 완벽히 부합하는 게임 딱 3개만 고르세요.
추천 이유는 존댓말을 유지하되, 매우 유쾌하고 친근하며 재치 있는 말투로 작성해주세요. (예: "친구분들끼리 이거 하다가 우정 파괴되기 딱 좋습니다 ㅎㅎ", "초보자분들도 금방 적응하실 수 있는 갓겜이랍니다!")
인사말이나 부연 설명은 절대 하지 말고, 오직 지정된 JSON 배열 포맷만 출력하세요."""

        user_prompt = f"""[우리 데이터베이스 목록 (스펙 포함)]
{game_list_str}

[상황]
{situation}

위 상황에 맞는 보드게임 3개를 추천해주세요. 
포맷: [{{"title": "...", "reason": "..."}}]"""

        url = gms_endpoint
        payload = {
            "model": "gpt-4o-mini", 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gms_key}"
        }
        
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        data = res.json()
        
        text = data['choices'][0]['message']['content']
        # Extract json using regex
        import re
        match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            text = text.replace("```json", "").replace("```", "").strip()
            
        result = json.loads(text)
        
        import xml.etree.ElementTree as ET
        
        fallback_image = "/boardgame_fallback.png"
        youtube_api_key = os.environ.get('YOUTUBE_API_KEY', '')
        bgg_key = os.environ.get('BGG_KEY', '')
        
        for item in result:
            title = item.get("title", "")
            item["image_url"] = fallback_image
            
            # DB에서 title로 game_id 검색
            game = BoardGames.objects.filter(title=title).first()
            if game:
                # 1순위: BGG API 시도
                try:
                    bgg_url = f"https://boardgamegeek.com/xmlapi2/thing?id={game.game_id}"
                    bgg_headers = {'Authorization': f'Bearer {bgg_key}'} if bgg_key else {}
                    bgg_res = requests.get(bgg_url, headers=bgg_headers, timeout=3)
                    if bgg_res.status_code == 200:
                        root = ET.fromstring(bgg_res.content)
                        thumb = root.find(".//thumbnail")
                        if thumb is not None and thumb.text:
                            item["image_url"] = thumb.text
                except Exception:
                    pass
                
                # 2순위: BGG 실패 시 YouTube 썸네일 시도
                if item["image_url"] == fallback_image and youtube_api_key:
                    try:
                        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
                        req = youtube.search().list(q=f"{title} 보드게임", part="snippet", type="video", maxResults=1)
                        yt_res = req.execute()
                        if yt_res['items']:
                            item["image_url"] = yt_res['items'][0]['snippet']['thumbnails']['high']['url']
                    except Exception as e:
                        print(f"YouTube Thumbnail Error for {title}: {e}")
        
        return JsonResponse({'recommendations': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
        game = BoardGames.objects.filter(title=title).first()
        if game:
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
