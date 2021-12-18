from django.db import models

# Model used for Database Table creation
class youtubeVideo(models.Model):
    videoId = models.CharField(max_length=256,primary_key=True)
    videoTitle = models.CharField(blank=False,max_length=100)
    description = models.TextField()
    publishDatetime = models.DateTimeField(blank=False)
    thumbnailURL = models.URLField()
    class Meta:
        indexes = [
            models.Index(fields=['videoId']),
            models.Index(fields=['publishDatetime'])
        ]
        get_latest_by = "publishDatetime"
        ordering = ['-publishDatetime']