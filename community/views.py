from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Article, Comment

def index(request):
    query = request.GET.get('q', '').strip()
    tag_filter = request.GET.get('tag', '').strip()
    articles = Article.objects.all().order_by('-created_at')
    
    if query:
        articles = articles.filter(
            Q(content__icontains=query) | Q(user__username__icontains=query)
        )
        
    if tag_filter:
        articles = articles.filter(tags__name=tag_filter)
        
    articles = articles.prefetch_related('comments__user', 'user', 'like_users', 'tags').distinct()
    
    context = {
        'articles': articles,
        'query': query,
        'tag_filter': tag_filter,
    }
    return render(request, 'community/index.html', context)

@require_POST
@login_required
def comment_create(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)
    content = request.POST.get('content', '').strip()
    if content:
        comment = Comment(article=article, user=request.user, content=content)
        comment.save()
    return redirect('community:index')

@require_POST
@login_required
def comment_delete(request, article_pk, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk, article_id=article_pk)
    if request.user == comment.user:
        comment.delete()
    return redirect('community:index')


@require_POST
@login_required
def like(request, review_pk):
    article = get_object_or_404(Article, pk=review_pk)
    
    if request.user in article.like_users.all():
        article.like_users.remove(request.user)
        is_liked = False
    else:
        article.like_users.add(request.user)
        is_liked = True
        
    context = {
        'is_liked': is_liked,
        'like_count': article.like_users.count(),
    }
    return JsonResponse(context)

@require_POST
@login_required
def create(request):
    content = request.POST.get('content')
    if content:
        article = Article(user=request.user, content=content)
        article.save()
    return redirect('community:index')

@require_http_methods(['GET', 'POST'])
@login_required
def update(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)
    if request.user != article.user:
        return HttpResponseForbidden()
        
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            article.content = content
            article.save()
            return redirect('community:index')
            
    context = {
        'article': article,
    }
    return render(request, 'community/update.html', context)

@require_POST
@login_required
def delete(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)
    if request.user == article.user:
        article.delete()
    return redirect('community:index')

@require_POST
def api_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)
        
    import json
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        game_title = data.get('game_title', '').strip()
        
        if not content:
            return JsonResponse({'status': 'error', 'message': '내용을 입력해주세요.'}, status=400)
            
        article = Article.objects.create(user=request.user, content=content)
        
        if game_title:
            from .models import Tag
            tag, _ = Tag.objects.get_or_create(name=game_title)
            article.tags.add(tag)
            
        return JsonResponse({'status': 'success', 'article_id': article.pk})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
