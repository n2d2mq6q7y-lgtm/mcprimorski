from django.shortcuts import render, get_object_or_404
from .models import Article


def article_list(request):
    articles = Article.objects.filter(published=True).order_by('-created_at')
    return render(request, 'publications/list.html', {'articles': articles})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, published=True)
    return render(request, 'publications/detail.html', {'article': article})
