from api.models import youtubeVideo
import asyncio
import concurrent.futures
import json
import tracemalloc
from datetime import datetime, timedelta
import os
from django.db import Error


# Background task to be run

# If want to run this task using Celery uncomment below code
""" from celery import shared_task
@shared_task """
def youtubeVideoList():
    # We can either use sync API call using googles official client library
    # or we can use other open source libraries
    # such as aiohttp to make async API call and improve performance

    # Async API call using asyncio and aiohttp
    """ try:
        curr_loop = asyncio.get_event_loop()
    except:
        curr_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(curr_loop)
    
    curr_loop.run_until_complete(fetchStoreVideosAsync()) """

    # Sync call
    fetchStoreVideosSync()


# Sync API call function
def fetchStoreVideosSync():
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from time import sleep

    # For profiling the memory usage of task [ For Developmet Only ]
    # as we are fetching json response which can be of size 1GB 
    # so use appropriate maxResults value to meet the RAM needs
    tracemalloc.start()
    maxResults = 100

    # Building youtube client
    # DEVELOPER_KEY is space separated list of API Keys
    # e.g. API_KEY_1 API_KEY_2
    # Converting "DEVELOPER_KEY" String into tuple
    DEVELOPER_KEY = tuple(os.environ['DEVELOPER_KEY'].split())
    KEY_INDEX = 0 # For keeping track of keys used 
    youtubeClient = build('youtube', 'v3', developerKey=DEVELOPER_KEY[KEY_INDEX])

    # Getting latest and earliest video's publish date-time from our stored database
    try:
        latestPublishDatetime = youtubeVideo.objects.latest().publishDatetime
        earliestPublishDatetime = youtubeVideo.objects.earliest().publishDatetime
    except:
        latestPublishDatetime = datetime.now().astimezone()
        earliestPublishDatetime = latestPublishDatetime

    # Assumed Earliest Datetime
    assumedEarliestDatetime = datetime(year=2021,month=1,day=1)
    # For keeping track of latest video from API result
    API_latestVideoPublishDatetime= ""

    # If earliest video is publish on "2021-01-01T00:00:00Z" 
    # then we have covered all old videos and can go for only latest videos published after latestPublishDatetime
    # Else
    # we have to store old videos which are published before database's earliest video's publish date-time
    if earliestPublishDatetime == assumedEarliestDatetime:
        publishedAfter = latestPublishDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        publishedBefore = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        # If, both are same, we will not get appropriate results, 
        # So wait for 10 seconds
        if publishedAfter == publishedBefore:
            publishedBefore = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        publishedAfter = assumedEarliestDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        publishedBefore = earliestPublishDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Printing Publish after/before for getting insights of progress
    print("\n\n ==== Publish Before:", publishedBefore, "====")
    print(" ==== Publish After:", publishedAfter, "==== \n\n")

    # For keeping track of next Page token
    nextPageToken = ""

    # To run forever
    while(True):
        # Wait for 10 seconds
        sleep(10)
        
        try:
            # Call the search.list method to retrieve results matching the specified
            # query term.
            searchResult = youtubeClient.search().list(
                part = "snippet",
                maxResults = maxResults,
                order = "date",
                pageToken = nextPageToken,
                publishedAfter = publishedAfter,
                publishedBefore = publishedBefore,
                q = "cricket",
                type = "video"
            ).execute()

        except HttpError as e:
            # Print HTTP error
            response = json.loads(e.content)
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, json.dumps(response,indent=2)))

            # Check if quota exceeded for given key then use next key
            if response['error']['errors'][0]['reason'] == 'quotaExceeded':
                KEY_INDEX += 1
                # If all keys are used and quota is exceeded then terminate the task
                if KEY_INDEX == len(DEVELOPER_KEY):
                    print("\n\n==== All Key's Quota Exceeded ====\n\n")
                    return
                youtubeClient = build('youtube', 'v3', developerKey=DEVELOPER_KEY[KEY_INDEX])
            # Continue the loop
            continue

        # Storing video details to database
        # Here we considering all recieved videos are new
        # but if not we will got to except block
        # We are using bulk creation which reduce SQL hits 
        # and reduce time consume by individual creation
        try:
            youtubeVideo.objects.bulk_create([
                youtubeVideo(
                    videoId = video['id']['videoId'],
                    videoTitle = video['snippet']['title'],
                    description = video['snippet']['description'],
                    publishDatetime = video['snippet']['publishedAt'],
                    thumbnailURL = video['snippet']['thumbnails']['high']['url']
                )
                for video in searchResult.get('items', [])
            ])

        except:
            # retrive complete list from stored database, 
            # which are published between the recieved result latest and earliest publish time
            storedVideoIdList = youtubeVideo.objects.filter(
                publishDatetime__lte = searchResult['items'][0]['snippet']['publishedAt'], 
                publishDatetime__gte = searchResult['items'][9]['snippet']['publishedAt']
            ).values_list('videoId',flat=True)

            # For storing the Models object for bulk create
            bulkObjectList = list()
            for video in searchResult.get('items', []):

                # If video is not present in stored video,
                # then append it to bulkObjectList
                if video['id']['videoId'] not in storedVideoIdList:
                    bulkObjectList.append(
                        youtubeVideo(
                            videoId = video['id']['videoId'],
                            videoTitle = video['snippet']['title'],
                            description = video['snippet']['description'],
                            publishDatetime = video['snippet']['publishedAt'],
                            thumbnailURL = video['snippet']['thumbnails']['high']['url']
                        )
                    )
            
            # If object list is not empty then perform bulk creation
            if bulkObjectList:
                youtubeVideo.objects.bulk_create(bulkObjectList)

        # If we update latest videos according to database 
        # then we will go for more latest videos but 
        # latestPublishDatetime have old value which should be updated, 
        # here we use search result instead of hitting SQL
        if not nextPageToken and searchResult['items']:
            API_latestVideoPublishDatetime = datetime.strptime(
                searchResult['items'][0]['snippet']['publishedAt'],
                '%Y-%m-%dT%H:%M:%S%z'
            )
            if latestPublishDatetime < API_latestVideoPublishDatetime:
                latestPublishDatetime = API_latestVideoPublishDatetime

        # Updating nextPageToken for accessing next page
        # If we get nextPageToken in search result, 
        # then we can update it 
        # but if it is not present 
        # then we have reached the end of search result 
        # so, we wil update publishedAfter to latestPublishDatetime and search for latest videos
        if 'nextPageToken' in searchResult:
            nextPageToken = searchResult['nextPageToken']
        else:
            nextPageToken = ""
            publishedAfter = (latestPublishDatetime + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            # For Acknoledgement, that we have reached end of current result
            # now we will go for updated search query
            print('\n\n==== Reached End | New Publish After:', publishedAfter,"====\n\n")
            publishedBefore = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            # If, both are same, we will not get appropriate results, So wait for 10 seconds
            if publishedAfter == publishedBefore:
                publishedBefore = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Tracing Memory usage [ For Developmet Only ]
        CurrentMemoryUsage, PeakMemoryUsage = tracemalloc.get_traced_memory()
        print("Current Memory Uasge:",CurrentMemoryUsage/1024,"KB | Peak Memory Usage:",PeakMemoryUsage/1024,"KB")


# Function for Asynchronous Database Operations
async def AsyncDatabase(modelObject, args = None):
    # Getting Event loop for async operation
    try:
        curr_loop = asyncio.get_event_loop()
    except:
        curr_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(curr_loop)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Waiting asynchronously for operation
        if modelObject == youtubeVideo.objects.bulk_create:
            return await curr_loop.run_in_executor( executor, modelObject, args )
        elif modelObject ==youtubeVideo.objects.values_list('videoId', flat=True).filter:
            return await curr_loop.run_in_executor( executor, modelObject, 
                publishDatetime__lte = args[0], 
                publishDatetime__gte = args[1] )
        return await curr_loop.run_in_executor( executor, modelObject )

# Async API call Function
async def fetchStoreVideosAsync():
    from aiohttp import ClientSession

    # Creating Asynchronous http session
    session = ClientSession()

    # For profiling the memory usage of task [ For Developmet Only ]
    # as we are fetching json response which can be of size 1GB 
    # so use appropriate maxResults value to meet the RAM needs
    tracemalloc.start()
    maxResults = 10

    # DEVELOPER_KEY is space separated list of API Keys
    # e.g. API_KEY_1 API_KEY_2
    # Converting "DEVELOPER_KEY" String into tuple
    DEVELOPER_KEY = tuple(os.environ['DEVELOPER_KEY'].split())
    KEY_INDEX = 0 # For keeping track of keys used

    # Getting latest and earliest video's publish date-time from our stored database
    try:
        latestPublishDatetime = await AsyncDatabase(youtubeVideo.objects.latest)
        latestPublishDatetime = latestPublishDatetime.publishDatetime

        earliestPublishDatetime = await AsyncDatabase(youtubeVideo.objects.earliest)
        earliestPublishDatetime = earliestPublishDatetime.publishDatetime
    except:
        latestPublishDatetime = datetime.now().astimezone()
        earliestPublishDatetime = latestPublishDatetime

    # Assumed Earliest Datetime
    assumedEarliestDatetime = datetime(year=2021,month=1,day=1)
    # For keeping track of latest video from API result
    API_latestVideoPublishDatetime= ""

    # If earliest video is publish on "2021-01-01T00:00:00Z" 
    # then we have covered all old videos and can go for only latest videos published after latestPublishDatetime
    # Else
    # we have to store old videos which are published before database's earliest video's publish date-time
    if earliestPublishDatetime == assumedEarliestDatetime:
        publishedAfter = latestPublishDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        publishedBefore = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        # If, both are same, we will not get appropriate results, 
        # So wait for 10 seconds
        if publishedAfter == publishedBefore:
            publishedBefore = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        publishedAfter = assumedEarliestDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        publishedBefore = earliestPublishDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # For keeping track of next Page token
    nextPageToken = ""

    # To run forever
    while(True):
        # Asynchronous Wait for 10 seconds
        await asyncio.sleep(10)
    
        # API URL Building
        url = 'https://youtube.googleapis.com/youtube/v3/search?part=snippet&order=date&q=cricket&type=video'
        url = url + '&pageToken=' + nextPageToken
        url = url + '&maxResults=' + str(maxResults)
        url = url + '&publishedBefore=' + publishedBefore
        url = url + '&publishedAfter=' + publishedAfter
        url = url + '&key=' + DEVELOPER_KEY[KEY_INDEX]

        # Making Asynchronous request to API
        async with session.get(url) as resp:
            data = await resp.read()
        
        # Converting Byte data to dictionary
        searchResult = json.loads(data)

        # If we encounter HTTP error
        if 'error' in searchResult:
            # Print HTTP error
            print('An HTTP error %d occurred:\n%s' % (searchResult['error']['code'], json.dumps(searchResult,indent=2)))

            # Check if quota exceeded for given key then use next key
            if searchResult['error']['errors'][0]['reason'] == 'quotaExceeded':
                KEY_INDEX += 1
                # If all keys are used and quota is exceeded then terminate the task
                if KEY_INDEX == len(DEVELOPER_KEY):
                    print("\n\n==== All Key's Quota Exceeded ====\n\n")
                    return
            # Continue the loop
            continue
        
        # Storing video details to database
        # Here we considering all recieved videos are new
        # but if not we will got to except block
        # We are using bulk creation which reduce SQL hits 
        # and reduce time consume by individual creation
        try:
            print('In 1st Part')
            await AsyncDatabase(
                youtubeVideo.objects.bulk_create,
                [
                    youtubeVideo(
                        videoId = video['id']['videoId'],
                        videoTitle = video['snippet']['title'],
                        description = video['snippet']['description'],
                        publishDatetime = video['snippet']['publishedAt'],
                        thumbnailURL = video['snippet']['thumbnails']['high']['url']
                    )
                    for video in searchResult.get('items', [])
                ]
            )

        except Error as e:
            print('In 2nd Part: ',e)
            # retrive complete list from stored database, 
            # which are published between the recieved result latest and earliest publish time
            try:
                print("Inside block")
                storedVideoIdList = await AsyncDatabase(
                    youtubeVideo.objects.values_list('videoId', flat=True).filter,
                    (searchResult['items'][0]['snippet']['publishedAt'],
                    searchResult['items'][9]['snippet']['publishedAt'])
                )
            except BaseException as e:
                print("\n\n ==== Error ==== \n\n")
                
            # For storing the Models object for bulk create
            bulkObjectList = list()
            for video in searchResult.get('items', []):

                # If video is not present in stored video,
                # then append it to bulkObjectList
                if video['id']['videoId'] not in storedVideoIdList:
                    bulkObjectList.append(
                        youtubeVideo(
                            videoId = video['id']['videoId'],
                            videoTitle = video['snippet']['title'],
                            description = video['snippet']['description'],
                            publishDatetime = video['snippet']['publishedAt'],
                            thumbnailURL = video['snippet']['thumbnails']['high']['url']
                        )
                    )
            
            # If object list is not empty then perform bulk creation
            if bulkObjectList:
                await AsyncDatabase(youtubeVideo.objects.bulk_create, bulkObjectList)

        # If we update latest videos according to database 
        # then we will go for more latest videos but 
        # latestPublishDatetime have old value which should be updated, 
        # here we use search result instead of hitting SQL
        if not nextPageToken and searchResult['items']:
            API_latestVideoPublishDatetime = datetime.strptime(
                searchResult['items'][0]['snippet']['publishedAt'],
                '%Y-%m-%dT%H:%M:%S%z'
            )
            if latestPublishDatetime < API_latestVideoPublishDatetime:
                latestPublishDatetime = API_latestVideoPublishDatetime

        # Updating nextPageToken for accessing next page
        # If we get nextPageToken in search result, 
        # then we can update it 
        # but if it is not present 
        # then we have reached the end of search result 
        # so, we wil update publishedAfter to latestPublishDatetime and search for latest videos
        if 'nextPageToken' in searchResult:
            nextPageToken = searchResult['nextPageToken']
        else:
            nextPageToken = ""
            publishedAfter = (latestPublishDatetime + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            publishedBefore = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            # If, both are same, we will not get appropriate results, So wait for 10 seconds
            if publishedAfter == publishedBefore:
                publishedBefore = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Tracing Memory usage [ For Developmet Only ]
        CurrentMemoryUsage, PeakMemoryUsage = tracemalloc.get_traced_memory()
        print("Current Memory Uasge:",CurrentMemoryUsage/1024,"KB | Peak Memory Usage:",PeakMemoryUsage/1024,"KB")