# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import django.contrib.auth
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.template import loader

from django.contrib.auth.decorators import login_required
from .models import *

from translate_api.translate_api import api as translate_api

from string import ascii_uppercase

import requests
import json
from html.parser import HTMLParser

@login_required(redirect_field_name=None)
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')
    template = loader.get_template('index.html')
    own_articles = [ (a.id, a.title) for a in Article.objects.filter(uploader=request.user)]
    latest_articles = [ (a.id, a.title) for a in Article.objects.all()][0:5]

    s,_ = Statistics.objects.get_or_create(user=request.user)

    context = {
        'guest' : False,
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
    article = get_object_or_404(Article, uploader=request.user, id=article_id)
    template = loader.get_template('article.html')
    context = {
        'title' : article.title,
        'article_text' : article.contents,
    }
   
    return HttpResponse(template.render(context, request))


@login_required(redirect_field_name=None)
def article_summary(request):
    words = request.POST["words"].split(',')

    session_num = Statistics.objects.get(user=request.user).srs_sessions

    for word in words:
        print(word)
        lit = word
        trn = get_object_or_404(Word, literal=word).translated
        obj, created = Word.objects.get_or_create(literal=lit, translated=trn)
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

        wp.easy_factor = max(1.3, wp.easy_factor)
        s.total_reviews += 1

        wp.next_review = s.srs_sessions + wp.interval

        wp.save()
    s.save()

    return HttpResponseRedirect('/')


class WiktionaryParser(HTMLParser): # TODO przenieść to osobnego modułu

    german_found = False
    searched_ids = ["Noun", "Verb", "Adjective", "Adverb", "Conjunction", "Pronoun", "Contraction", "Numeral", "Article", "Preposition"]
    expect_list = False
    expect_translation = False
    result = ""
   
    def handle_starttag(self, tag, attrs):
        if self.expect_list:
            if tag == 'li':
                self.expect_translation = True
            elif tag == 'dl':
                self.expect_translation = False
                self.expect_list = False
                self.german_found = False
        elif tag == "span" and ('id', 'German') in attrs:
            self.german_found = True
        elif tag == "hr":
            self.german_found = False

    def handle_endtag(self, tag):
        if self.expect_translation and tag == "li" and self.result != "":
            self.expect_translation = False
            self.expect_list = False
            self.german_found = False
        
    def handle_data(self, data):
        if self.expect_translation:
            self.result += data
        elif self.german_found:
            if data in self.searched_ids:
                self.expect_list = True

def translate(request):
    print(request.GET)
    word = request.GET['w']
    def handle_word(word):
        translation_url = "https://translate.googleapis.com/translate_a/single?client=brt&sl=de&tl=pl&q=" + word + "&ie=UTF-8&oe=UTF-8"

        result = translate_api( word, "de", "pl" )

        #req = requests.get(translation_url)
        #print(req.text)
        #wp = WiktionaryParser()
        #wp.feed(req.text)
        #result = req.text # wp.result
        print(result)
        if result == "":
            result = "Not found"
        return (word, result)
    (word, translation) = handle_word(word)
    obj, created = Word.objects.get_or_create(literal=word, translated=translation)
    if created:
        obj.save()
    return JsonResponse({'yourword': word, 'translation': translation})


@login_required(redirect_field_name=None)
def article_submit(request):
    print(request.POST)
    if request.user.is_authenticated:
        a = Article(uploader=request.user, title=request.POST['article_title'], contents=request.POST['article_text'])
        a.save()
        return HttpResponseRedirect("/article/"+str(a.id))
    return HttpResponseRedirect("/login") 


