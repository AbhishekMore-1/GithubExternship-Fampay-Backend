from api.models import youtubeVideo
import asyncio
import json
import tracemalloc
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
from django.db import Error
from asgiref.sync import sync_to_async
from django.utils.dateparse import parse_datetime


# Background task to be run

# If want to run this task using Celery uncomment below code
""" from celery import shared_task
@shared_task """
def youtubeVideoList():
    # We can either use sync API call using googles official client library
    # or we can use other open source libraries
    # such as aiohttp to make async API call and improve performance

    # Async API call using asyncio and aiohttp
    try:
        curr_loop = asyncio.get_event_loop()
    except:
        curr_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(curr_loop)
    
    curr_loop.run_until_complete(fetchStoreVideosAsync())

    # Sync call
    """ fetchStoreVideosSync() """


# Sync API call function
def fetchStoreVideosSync():
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from time import sleep

    # Waiting for Django App to start completely
    sleep(10)

    # For profiling the memory usage of task [ For Developmet Only ]
    # as we are fetching json response which can be of size 1GB 
    # so use appropriate maxResults value to meet the RAM needs
    """ tracemalloc.start() """
    # I don't find any memory leak or high memory consumption from this function after testing
    maxResults = 100

    # DEVELOPER_KEY is space separated list of API Keys
    # e.g. API_KEY_1 API_KEY_2
    # Converting "DEVELOPER_KEY" String into tuple
    DEVELOPER_KEY = tuple(os.environ['DEVELOPER_KEY'].split())
    KEY_INDEX = 0 # For keeping track of keys used 

    # Building youtube client
    youtubeClient = build('youtube', 'v3', developerKey=DEVELOPER_KEY[KEY_INDEX])

    # Getting latest and earliest video's publish date-time from our stored database
    try:
        latestPublishDatetime = youtubeVideo.objects.latest().publishDatetime
        earliestPublishDatetime = youtubeVideo.objects.earliest().publishDatetime
    except:
        latestPublishDatetime = datetime.now(timezone.utc)
        earliestPublishDatetime = latestPublishDatetime

    # Assumed Earliest Datetime
    assumedEarliestDatetime = datetime(year=2021,month=12,day=12,tzinfo=timezone.utc)
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
                type = "video",
                eventType="completed"
            ).execute()

        except HttpError as e:
            # Print HTTP error
            response = json.loads(e.content)
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, json.dumps(response,indent=2)))

            # Check if quota exceeded for given key then use next key
            if response['error']['errors'][0]['reason'] == 'quotaExceeded':
                KEY_INDEX += 1

                # If all keys are used and quota is exceeded then wait for API quota reset
                if KEY_INDEX == len(DEVELOPER_KEY):
                    print("\n\n==== All Key's Quota Exceeded ====")
                    print("==== Waiting for Quota to rest ====")

                    # Calculating time remaining for quota reset i.e. Midnight Pacific time
                    currTime = datetime.now().astimezone().astimezone(ZoneInfo("US/Pacific"))
                    tomorrowMidnight = (currTime + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
                    waitingTime = tomorrowMidnight - currTime
                    print("==== Waiting for",waitingTime,"====")

                    # Waiting for API key's quota to reset
                    sleep(waitingTime.total_seconds())

                    print("\n\n==== Key's Quota Reset ====")
                    print("==== Starting Background Task ====\n\n")
                    KEY_INDEX = 0
                
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

        except Error as e:
            # To keep track of how many errors are occuring
            # helpful for optimising algorithm 
            print(e)
            # retrive complete list from stored database, 
            # which are published between the recieved result's latest and earliest publish time
            storedVideoIdList = youtubeVideo.objects.filter(
                publishDatetime__lte = searchResult['items'][0]['snippet']['publishedAt'], 
                publishDatetime__gte = searchResult['items'][-1]['snippet']['publishedAt']
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
            API_latestVideoPublishDatetime = parse_datetime(searchResult['items'][0]['snippet']['publishedAt'])
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
        """ CurrentMemoryUsage, PeakMemoryUsage = tracemalloc.get_traced_memory()
        print("Current Memory Uasge:",round(CurrentMemoryUsage/1024, 2),"KB | Peak Memory Usage:",round(PeakMemoryUsage/1024, 2),"KB") """

        # Printing
        if searchResult['items']:
            print("Cycle completed | Publish Datetime Span:",searchResult['items'][0]['snippet']['publishedAt'],"to",searchResult['items'][-1]['snippet']['publishedAt'])



# Async API call Function
async def fetchStoreVideosAsync():
    from aiohttp import ClientSession, ClientError

    # Waiting for Django App to start completely
    await asyncio.sleep(10)

    # For profiling the memory usage of task [ For Developmet Only ]
    # as we are fetching json response which can be of size 1GB 
    # so use appropriate maxResults value to meet the RAM needs
    tracemalloc.start()
    # I don't find any memory leak or high memory consumption from this function after testing
    maxResults = 50

    # DEVELOPER_KEY is space separated list of API Keys
    # e.g. API_KEY_1 API_KEY_2
    # Converting "DEVELOPER_KEY" String into tuple
    DEVELOPER_KEY = tuple(os.environ['DEVELOPER_KEY'].split())
    KEY_INDEX = 0 # For keeping track of keys used

    # Creating Asynchronous http session
    session = ClientSession()

    # Assumed Earliest Datetime
    # For Keeping track of previous search result's earliest datetime
    # Let, our task interrupted before saving all results to database
    # then we must store the remaining result in next boot
    # for that purpose, I have used text file for storing single datetime value
    filePath = os.path.join( os.path.dirname(__file__), 'assumedEarliestDatetime.txt' )
    # If file exist, then read value
    if(os.path.exists(filePath)):
        filePointer = open(filePath)
        assumedEarliestDatetime = parse_datetime(filePointer.read())
        filePointer.close()
    # Otherwise create file, write and use predefined value
    else:
        filePointer = open(filePath,"w")
        assumedEarliestDatetime = datetime(year=2021,month=12,day=23,tzinfo=timezone.utc)
        filePointer.write("2021-12-23T00:00:00Z")
        filePointer.close()

    # Getting latest and earliest video's publish date-time from our stored database
    try:
        latestPublishDatetime = await sync_to_async(youtubeVideo.objects.latest)()
        latestPublishDatetime = latestPublishDatetime.publishDatetime
        # Finding the Earliest Publish Datetime which is after Assumed Earliest Datetime 
        earliestPublishDatetime = await sync_to_async(youtubeVideo.objects.filter(publishDatetime__gte = assumedEarliestDatetime).earliest)()
        earliestPublishDatetime = earliestPublishDatetime.publishDatetime
    except:
        latestPublishDatetime = datetime.now(timezone.utc)
        earliestPublishDatetime = latestPublishDatetime

    # We are always considering old videos or searching for old videos,
    # because there are chances that we may miss some videos 
    # with same Publish Datetime as Assumed Earliest Datetime & Earliest Publish Datetime
    publishedAfter = assumedEarliestDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    # For keeping track of result's previous page's earliest datetime
    previousPageEarliestDatetime = earliestPublishDatetime

    # If Earliest Publish Datetime from database (earliestPublishDatetime) is same as 
    # Earliest Publish Datetime from prvious search result (assumedEarliestDatetime)
    # then we will wait for 10 seconds
    previousPageEarliestDatetime += timedelta(seconds=10) if earliestPublishDatetime == assumedEarliestDatetime else timedelta()
    publishedBefore = previousPageEarliestDatetime.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Printing Publish after/before for getting insights of progress
    print("\n\n ==== Publish Before:", publishedBefore, "====")
    print(" ==== Publish After:", publishedAfter, "==== \n\n")

    # For keeping track of next Page token
    nextPageToken = ""

    # To run forever
    while(True):
        YoutubeAPIErrorCount = 0
        # Asynchronous Wait for 10 seconds
        await asyncio.sleep(10)
    
        # API URL Building
        url = 'https://youtube.googleapis.com/youtube/v3/search?part=snippet&order=date&q=cricket&type=video&eventType=completed'
        url = url + '&pageToken=' + nextPageToken
        url = url + '&maxResults=' + str(maxResults)
        url = url + '&publishedBefore=' + publishedBefore
        url = url + '&publishedAfter=' + publishedAfter
        url = url + '&key=' + DEVELOPER_KEY[KEY_INDEX]

        # Making Asynchronous request to API
        try:
            async with session.get(url) as response:
                searchResult = await response.json()
        except ClientError as e:
            print("A HTTP Client Error Occured:",e)
            continue

        # If we encounter HTTP error
        if 'error' in searchResult:
            # Print HTTP error
            print('An HTTP error %d occurred:\n%s' % (searchResult['error']['code'], json.dumps(searchResult,indent=2)))

            # Check if quota exceeded for given key then use next key
            if searchResult['error']['errors'][0]['reason'] == 'quotaExceeded':
                KEY_INDEX += 1

                # If all keys are used and quota is exceeded then wait for API quota reset
                if KEY_INDEX == len(DEVELOPER_KEY):
                    print("\n\n==== All Key's Quota Exceeded ====")
                    print("==== Waiting for Quota to rest ====")

                    # Closing http session to free up memory
                    await session.close()

                    # Calculating time remaining for quota reset i.e. Midnight Pacific time
                    currTime = datetime.now().astimezone().astimezone(ZoneInfo("US/Pacific"))
                    tomorrowMidnight = (currTime + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
                    waitingTime = tomorrowMidnight - currTime
                    print("==== Waiting for",waitingTime,"time ====\n\n")

                    # Asynchronously waiting for API key's quota reset
                    await asyncio.sleep(waitingTime.total_seconds())

                    # Restarting the http client
                    session = ClientSession()
                    print("\n\n==== Key's Quota Reset ====")
                    print("==== Starting Background Task ====\n\n")
                    KEY_INDEX = 0
            # Continue the loop
            continue

        # For keeping track of oldest/latest video from API result's current page
        API_oldestVideoPublishDatetime = datetime.now(timezone.utc)
        API_latestVideoPublishDatetime = datetime.min.replace(tzinfo=timezone.utc)

        # We are filtering the search result as Youtube Data API sometime doesn't follow query parameters
        # Here we are filtering the search result for published before and published after parameter
        # Also, pagination give result from previous page. To handle this, we are also mainting
        # variable previousPageEarliestDatetime
        # We are using bulk creation which reduce SQL hits 
        # and reduce time consume by individual creation
        bulkObjectList = list()

        for video in searchResult.get('items', []):

            videoPublishedAt = parse_datetime(video['snippet']['publishedAt'])
            # Checking whether the video is published between previousPageEarliestDatetime and publishedAfter
            if videoPublishedAt <= previousPageEarliestDatetime and videoPublishedAt >= parse_datetime(publishedAfter):

                # Updating the API_oldestVideoPublishDatetime to oldest video
                if videoPublishedAt < API_oldestVideoPublishDatetime:
                    API_oldestVideoPublishDatetime = videoPublishedAt
                # Updating the API_latestVideoPublishDatetime to latest video
                if videoPublishedAt > API_latestVideoPublishDatetime:
                    API_latestVideoPublishDatetime = videoPublishedAt
                
                bulkObjectList.append(
                    youtubeVideo(
                        videoId = video['id']['videoId'],
                        videoTitle = video['snippet']['title'],
                        description = video['snippet']['description'],
                        publishDatetime = videoPublishedAt,
                        thumbnailURL = video['snippet']['thumbnails']['high']['url']
                    )
                )
            else:
                YoutubeAPIErrorCount+=1

        try:
            await sync_to_async(youtubeVideo.objects.bulk_create)(bulkObjectList)

        except Error as e:
            # To keep track of how many errors are occuring
            # helpful for optimising algorithm 
            print(e)

            # retrive complete list from stored database, 
            # which are published between the API_latestVideoPublishDatetime and API_oldestVideoPublishDatetime
            tempQuery = youtubeVideo.objects.filter(
                        publishDatetime__lte = API_latestVideoPublishDatetime, 
                        publishDatetime__gte = API_oldestVideoPublishDatetime
                    ).values_list('videoId',flat=True)
            
            storedVideoIdList = await sync_to_async(set)(tempQuery)

            # If Youtube API pagination gives previous page videos with same published datetime as previousPageEarliestDatetime
            # Then we have to look into video IDs for filtering them out
            newBulkObjectList = list()
            for video in bulkObjectList:
                # If video is not present in stored video,
                # then append it to newBulkObjectList
                if video.videoId not in storedVideoIdList:
                    newBulkObjectList.append(video)
                else:
                    YoutubeAPIErrorCount+=1
            
            try:
                await sync_to_async(youtubeVideo.objects.bulk_create)(newBulkObjectList)

            except:
                # If Youtube API didn't followed the event type contraint
                # then for handling this, we have to go through each video's ID in database
                # Youtube update the publishedAt attribute of video which are of type live/upcoming,
                # when the user makes some updates in the video
                tempQuery = youtubeVideo.objects.filter(
                            videoId__in= [ video.videoId for video in newBulkObjectList ]
                        ).values_list('videoId',flat=True)
                
                sameVideoAsDatabase = await sync_to_async(set)(tempQuery)

                print("Youtube API Error | Same Video found:")
                print(sameVideoAsDatabase)

                # For storing the Models object for bulk create
                bulkObjectList = list()
                for video in newBulkObjectList:
                    # If video is not present in stored video,
                    # then append it to bulkObjectList
                    if video.videoId not in sameVideoAsDatabase:
                        bulkObjectList.append(video)
                    else:
                        YoutubeAPIErrorCount+=1
                
                await sync_to_async(youtubeVideo.objects.bulk_create)(bulkObjectList)
        

        # Updating the value of previousPageEarliestDatetime, so it will be used for filtering the next result page
        previousPageEarliestDatetime = API_oldestVideoPublishDatetime
        
        # If we update latest videos according to database 
        # then we will go for more latest videos but 
        # latestPublishDatetime have old value which should be updated, 
        # here we use search result instead of hitting SQL
        if searchResult['items']:
            # Printing Datetime span, for which videos are stored in database
            print("Error Count:",YoutubeAPIErrorCount,"| Publish Datetime Span:",API_latestVideoPublishDatetime,"to",API_oldestVideoPublishDatetime)

            if not nextPageToken and latestPublishDatetime < API_latestVideoPublishDatetime:
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

            # Updating Assumed Earliest Datetime
            filePointer = open(filePath,"w")
            filePointer.write(publishedAfter)
            filePointer.close()

            # Updating publishedBefore to current UTC time 
            publishedBefore = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            # If, both are same, we will not get appropriate results, So wait for 10 seconds
            if publishedAfter == publishedBefore:
                publishedBefore = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Tracing Memory usage [ For Developmet Only ]
        CurrentMemoryUsage, PeakMemoryUsage = tracemalloc.get_traced_memory()
        print("Current Memory Uasge:",round(CurrentMemoryUsage/1024, 2),"KB | Peak Memory Usage:",round(PeakMemoryUsage/1024, 2),"KB")