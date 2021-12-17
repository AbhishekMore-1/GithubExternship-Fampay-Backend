import asyncio
from celery import shared_task

# Asynchronous background task to be run
@shared_task
def youtubeVideoList():
    try:
        curr_loop = asyncio.get_event_loop()
    except:
        curr_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(curr_loop)
    curr_loop.run_until_complete(backgroundTask())

async def backgroundTask():
    counter = 0
    while(True):
        counter += 1
        print("Hello",counter)
        await asyncio.sleep(2)