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
        gms_endpoint = os.environ.get('GMS_ENDPOINT', 'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent')
        summary = "AI 요약 기능을 사용할 수 없습니다. (API KEY 누락)"
        if gms_key:
            prompt = f"보드게임 '{game.title}'의 핵심 승리 조건과 턴 진행 방식을 3~4줄로 요약해줘."
            url = f"{gms_endpoint}?key={gms_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}
            
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=60)
                res.raise_for_status()
                data = res.json()
                summary = data['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                summary = f"AI 호출 중 오류가 발생했습니다: {str(e)}"
                print("Gemini API Error:", res.text if 'res' in locals() else e)
            
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
            
        # DB에 있는 게임 목록 가져오기 (토큰 수 제한을 고려하여 인기 순 최대 300개로 제한)
        db_games = list(BoardGames.objects.order_by('rank').values_list('title', flat=True)[:300])
        game_list_str = ", ".join(db_games) if db_games else "(현재 DB에 게임이 없습니다)"
        
        prompt = f"다음은 우리 데이터베이스에 있는 보드게임 목록입니다: {game_list_str}\n\n이 목록에 있는 게임들 중에서만, 다음 상황에 맞는 보드게임 3개를 골라 추천해주고 이유를 짧게 설명해줘. 상황: {situation}. 인사말이나 부연 설명 없이 오직 JSON 배열만 출력해줘. 포맷: [{{\"title\": \"...\", \"reason\": \"...\"}}]"
        url = gms_endpoint
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
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
        'ai_summary': summary
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
