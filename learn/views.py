# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import django.contrib.auth
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.template import loader

from django.contrib.auth.decorators import login_required
from .models import *

import json
from translate_api.translate_api import api as translate_api

@login_required(redirect_field_name=None)
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')
    template = loader.get_template('index.html')
    own_articles = [ (a.id, a.language, a.title, a.contents[0:100]+"...") for a in Article.objects.filter(uploader=request.user)[::-1][0:3]]
    latest_articles = [ (a.id, a.language, a.title, a.contents[0:100]+"...") for a in Article.objects.all()[::-1][0:3]]

    s = Statistics.objects.get(user=request.user)

    context = {
        'own_articles' : own_articles,
        'latest_articles' : latest_articles,
        'stats' : s,
    }
    return HttpResponse(template.render(context, request))


def login(request):
    template = loader.get_template('login.html')
    ucf = UserCreationForm()

    if request.method == 'POST':
        if request.POST['type'] == 'signup':
            print(request.POST)
            ucf = UserCreationForm(request.POST)
            if ucf.is_valid():
                ucf.save()
                username = request.POST.get('username', None)
                password = request.POST.get('password1', None)
                user = django.contrib.auth.authenticate(request, username=username, password=password)
                django.contrib.auth.login(request, user)

                s,_ = Statistics.objects.get_or_create(user=user)
                s.save()

                return HttpResponse(template.render({'status': 'Sign up successful'}, request))
            return HttpResponse(template.render({'form': ucf, 'status': 'Sign up failed'}, request))
        elif request.POST['type'] == 'login':
            username = request.POST.get('username', None)
            password = request.POST.get('password', None)
            user = django.contrib.auth.authenticate(request, username=username, password=password)
            if user is not None: # sukces
                django.contrib.auth.login(request, user)
                return HttpResponseRedirect('/')
            else: # błąd
                print(request)
                return HttpResponse(template.render({'form': ucf, 'status': 'Login attempt failed.'}, request))
    # brak próby
    return HttpResponse(template.render({'form': ucf}, request))


def logout(request):
    django.contrib.auth.logout(request)
    template = loader.get_template('login.html')
    return HttpResponseRedirect('/login', template.render({'status': 'You\'ve been logged out.'}, request))


@login_required(redirect_field_name=None)
def article_new(request):
    template = loader.get_template('article_new.html')
    return HttpResponse(template.render({}, request))


@login_required(redirect_field_name=None)
def article(request, article_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')
    article = get_object_or_404(Article, id=article_id)
    template = loader.get_template('article.html')
    context = {
            'article': article,
    }
   
    return HttpResponse(template.render(context, request))


@login_required(redirect_field_name=None)
def article_summary(request):
    words = filter( lambda x: x != '', request.POST["words"].split(','))
    lang = request.POST["article_language"]
    print(words, lang)

    session_num = Statistics.objects.get(user=request.user).srs_sessions

    for word in words:
        print(word)
        trn = get_object_or_404(Word, literal=word, language=lang).translated
        obj, created = Word.objects.get_or_create(literal=word, translated=trn, language=lang)

        WordProgress.objects.filter(word=obj, user=request.user).delete()
        wp = WordProgress(word=obj, user=request.user, next_review=session_num+1)

        wp.save()

    return HttpResponseRedirect('/')


@login_required(redirect_field_name=None)
def spaced_repetition(request):
    template = loader.get_template('srs.html')
    # get srs count from stats

    stats = Statistics.objects.get(user=request.user)

    words_p = WordProgress.objects.filter(user=request.user, next_review=stats.srs_sessions+1)
    js_data = [ (wp.word.literal, wp.word.translated, wp.id) for wp in words_p ]

    if WordProgress.objects.filter(user=request.user).count() == 0:
        context = { "error" : "Brak słów. Przeczytaj artykuł i dodaj kilka." }
        return HttpResponse(template.render(context, request))

    while len(js_data) == 0:
        # jeżeli nie było nic do powtórki przy tej sesji to zwiększamy licznik o jeden
        # i bierzemy słowa z kolejnej sesji
        stats.srs_sessions += 1
        words_p = WordProgress.objects.filter(user=request.user, next_review=stats.srs_sessions+1)
        js_data = [ (wp.word.literal, wp.word.translated, wp.id) for wp in words_p ]

    stats.save()

    context = { "words" : json.dumps(js_data) }
    return HttpResponse(template.render(context, request))


@login_required(redirect_field_name=None)
def spaced_repetition_summary(request):
    results = request.POST['results']
    s = Statistics.objects.get(user=request.user)
    results = results.strip('[]() ').split(',')
    ids = map(int,results[0::2])
    scores = map(int,results[1::2])

    s.srs_sessions += 1

    for wp_id, score in zip(ids, scores):
        wp = WordProgress.objects.get(id=wp_id)
        if score == 1:
            wp.easy_factor -= 0.2
            wp.interval *= 0.5
            s.wrong_guesses += 1
        elif score == 2:
            wp.easy_factor -= 0.15
            wp.interval *= 1.2
        elif score == 3:
            wp.interval *= wp.easy_factor
        else: # 4
            wp.interval *= wp.easy_factor
            wp.easy_factor += 0.15

        wp.interval = round(max(1, wp.interval),2)
        wp.easy_factor = round(max(1.3, wp.easy_factor),2)
        wp.next_review = s.srs_sessions + wp.interval

        s.total_reviews += 1
        wp.save()
    s.save()

    return HttpResponseRedirect('/')


@login_required(redirect_field_name=None)
def word_list(request):
    template = loader.get_template('word_list.html')
    context = {
        'word_ps': WordProgress.objects.filter(user=request.user)
    }
    return HttpResponse(template.render(context,request))

@login_required(redirect_field_name=None)
def article_list(request):
    type = request.GET['type']
    template = loader.get_template('article_list.html')
    if type == 'all':
        articles = [ (a.id, a.language, a.title, a.contents[0:100]+"...") for a in Article.objects.all()]
    elif type == 'id':
        id = request.GET['id']
        user = User.objects.get(id=id)
        articles = [ (a.id, a.language, a.title, a.contents[0:100]+"...") for a in Article.objects.filter(uploader=user)]

    context = {
        'title' : 'Twoje artykuły' if type == 'mine' else 'Wszystkie artykuły',
        'articles' : articles,
    }
    return HttpResponse(template.render(context, request))

@login_required(redirect_field_name=None)
def article_submit(request):
    print(request.POST)
    if request.user.is_authenticated:
        a = Article(uploader=request.user, title=request.POST['article_title'], contents=request.POST['article_text'], language=request.POST['article_language'])
        a.save()
        return HttpResponseRedirect("/article/"+str(a.id))
    return HttpResponseRedirect("/login") 


def translate(request):
    print(request.GET)
    word = request.GET['w']
    lang = request.GET['lang']
    translation = translate_api( word, lang, "pl" )

    obj, created = Word.objects.get_or_create(literal=word, translated=translation, language=lang)
    if created:
        obj.save()
    return JsonResponse({'yourword': word, 'translation': translation})


@login_required(redirect_field_name=None)
def profile(request, user_id):
    template = loader.get_template('profile.html')
    user = User.objects.get(id=user_id)
    langs = list(set( [ wp.word.language for wp in WordProgress.objects.filter(user=user)] ))
    context = {
        'profile' : user,
        'stats' : Statistics.objects.get(user=user),
        'languages' : ', '.join(langs),
    }
    return HttpResponse(template.render(context, request))


@login_required(redirect_field_name=None)
def user_search(request):
    regex = request.GET['regex']
    template = loader.get_template('user_search.html')
    results = User.objects.filter(username__regex=regex)
    context = {
        'title' : "Wyniki dla '" + regex + "'",
        'users' : results,
    }
    return HttpResponse(template.render(context, request))

@login_required(redirect_field_name=None)
def remove_word(request, word_id):
    template = loader.get_template('word_list.html')
    w = WordProgress.objects.get(id=word_id, user=request.user)
    deleted = w.word.literal
    w.delete()
    context = {
        'message' : "Słowo '" + deleted + "' usunięto pomyślnie",
        'word_ps': WordProgress.objects.filter(user=request.user),
    }
    return HttpResponse(template.render(context,request))
    return HttpResponse(template.render(context, request))

