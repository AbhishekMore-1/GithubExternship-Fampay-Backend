from datetime import datetime
from .models import youtubeVideo
from rest_framework import viewsets, filters
from .serializers import youtubeSerializer
from rest_framework.pagination import PageNumberPagination

# Custom Pagination for better serving/view
class CustomPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'pageSize'
    max_page_size = 80

# Custom Filter for Publish After and Publish Before Option
class dateTimeFilter(filters.BaseFilterBackend):
    """
    Filter for Publish After and Publish Before Option
    """
    def filter_queryset(self, request, queryset, view):
        publishedAfter = request.GET.get('publishedAfter', "2021-01-01T00:00:00Z")
        print(publishedAfter)
        publishedBefore = request.GET.get('publishedBefore', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
        return queryset.filter(
            publishDatetime__lte = publishedBefore, 
            publishDatetime__gte = publishedAfter
        )
    
    # Not working the way it should
    # Not Found relevant solution for same
    """     
    def to_html(self, request, queryset, view):
        from rest_framework.response import Response
        return Response(template_name='dateTimeFilter.html')
     """

# Configuration for API and Browsable API view
class youtubeVideos(viewsets.ModelViewSet):
    """
    API endpoint that allows Youtube Video list to be viewed
    """
    # response sorted in descending order of published datetime
    queryset = youtubeVideo.objects.all().order_by('-publishDatetime')

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, dateTimeFilter)
    # Adding the search and filter fields
    search_fields = ['videoId', 'videoTitle', 'description', ]
    filter_fields = ['publishDatetime']
    ordering_fields = ['publishDatetime']
    serializer_class = youtubeSerializer
    pagination_class = CustomPagination