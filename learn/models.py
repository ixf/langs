from django.db import models
from django.contrib.auth.models import User

class Word(models.Model):
    literal = models.CharField(max_length=128)
    translated = models.CharField(max_length=512)

class WordProgress(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    easy_factor = models.FloatField(default=2.5)
    next_review = models.PositiveIntegerField()
    interval = models.PositiveIntegerField(default=1)

    wrong_guesses = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)

class Article(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    contents = models.TextField()

class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    srs_sessions = models.PositiveIntegerField(default=0)
    wrong_guesses = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    @property
    def correctness(self):
        if self.total_reviews == 0:
            return "N/A"
        return round(1.0-(self.wrong_guesses/self.total_reviews),4)
