from django.db import models

# Create your models here.

class Song(models.Model):

    title = models.CharField(max_length=500, null=True)
    artist = models.CharField(max_length=500, null=True)
    year = models.IntegerField(null=True)
    language = models.CharField(max_length=500, null=True)
    rdio_key = models.CharField(max_length=500, null=True)

    # emotions
    happy = models.IntegerField(default=0)
    angry = models.IntegerField(default=0)
    party = models.IntegerField(default=0)
    relaxed = models.IntegerField(default=0)
    sad = models.IntegerField(default=0)
    love = models.IntegerField(default=0)
    total_responses = models.IntegerField(default=0)

    def __str__(self):
        return self.title + '; ' + self.rdio_key

    def get_score(self, moods):
        total_percentage = 0.
        total_moods = len(moods)
        if total_moods == 0:
            return 0
        for mood in moods:
            value = getattr(self, mood)
            total_percentage += float(value) / float(self.total_responses)
        return float(total_percentage) / float(total_moods)

    def incr_score(self, mood, save=False):
        old_value = getattr(self, mood)
        setattr(self, mood, old_value+1)
        self.total_responses += 1
        if save:
            self.save()
