from django.db import models

# Model used for Database Table creation
class youtubeVideo(models.Model):
    videoTitle = models.CharField(blank=False,max_length=100)
    description = models.TextField()
    publishDatetime = models.DateTimeField(blank=False)
    thumbnailURL = models.URLField()