from .models import youtubeVideo
from rest_framework import viewsets, filters
from .serializers import youtubeSerializer
from rest_framework.pagination import PageNumberPagination

# Custom Pagination for better serving/view
class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'
    max_page_size = 1000


# Configuration for API and Browsable API view
class youtubeVideos(viewsets.ModelViewSet):
    """
    API endpoint that allows Youtube Video list to be viewed
    """
    # response sorted in descending order of published datetime
    queryset = youtubeVideo.objects.all().order_by('-publishDatetime')

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    # Adding the search and filter fields
    search_fields = ['videoId', 'videoTitle', 'description', ]
    filter_fields = ['publishDatetime']
    ordering_fields = ['publishDatetime']
    serializer_class = youtubeSerializer
    pagination_class = CustomPagination