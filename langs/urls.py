
from django.contrib import admin
from django.urls import path

from learn import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('login', views.login),
    path('logout', views.logout),
    path('article/new', views.article_new),
    path('article_submit', views.article_submit),
    path('article/<int:article_id>', views.article),
    path('article/summary', views.article_summary),
    path('article/summary/', views.article_summary),
    path('translate', views.translate),
    path('srs', views.spaced_repetition),
    path('srs/summary', views.spaced_repetition_summary),
    path('translate', views.translate),
]
