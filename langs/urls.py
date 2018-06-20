
from django.contrib import admin
from django.urls import path

from learn import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('login', views.login),
    path('logout', views.logout),
    path('article_new', views.article_new),
    path('article_list', views.article_list),
    path('article_submit', views.article_submit),
    path('article_summary', views.article_summary),
    path('article/<int:article_id>', views.article),
    path('translate', views.translate),
    path('srs', views.spaced_repetition),
    path('words', views.word_list),
    path('srs_summary', views.spaced_repetition_summary),
    path('translate', views.translate),
    path('user_search', views.user_search),
    path('profile/<int:user_id>', views.profile),
    path('remove_word/<int:word_id>', views.remove_word),
]
