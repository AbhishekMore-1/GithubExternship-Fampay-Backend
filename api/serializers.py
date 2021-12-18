from rest_framework import serializers
from .models import youtubeVideo

# Serializer for our model
# HyperlinkedModelSerializer provide URL for given object, which is more convinient to access object
class youtubeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = youtubeVideo
        fields = ('url', 'videoId', 'videoTitle', 'description', 'publishDatetime', 'thumbnailURL')