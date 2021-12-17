from .models import youtubeVideo
from rest_framework import viewsets
from .serializers import youtubeSerializer
from rest_framework.pagination import PageNumberPagination

# Custom Pagination for better serving/view
class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'
    max_page_size = 1000

class youtubeVideos(viewsets.ModelViewSet):
    """
    API endpoint that allows Youtube Video list to be viewed
    """
    # response sorted in descending order of published datetime
    queryset = youtubeVideo.objects.all().order_by('-publishDatetime')
    serializer_class = youtubeSerializer
    pagination_class = CustomPagination