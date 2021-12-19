# GithubExternship-Fampay-Backend
To make an API to fetch latest videos sorted in reverse chronological order of their publishing date-time from YouTube for a given tag/search query in a paginated response.

### Instruction for running the project

<ol>
   <li>Install Python 3.10</li>
   <li>Install pipenv</li>
    
    pip install pipenv
   <li>Create .venv folder to localize the python virtual environment</li>
    
    pipenv shell
   <li>Then install project dependacies by following command</li>
    
    pipenv install
   <li>Then exit from pipenv shell using following command</li>
    
    exit
   <li>Then migrate the django models using following command</li>

    python manage.py migrate
   <li>And fire up the server</li>
    
    python manage.py runserver
    
   We can access API at 

    http://127.0.0.1:8000/api/youtubeVideos/

   As it is browsable API, so we can access it through browser using same link and it support `page` & `pageSize` options

   Also, We can access specific video details by using its videoId like following
   
    http://127.0.0.1:8000/api/youtubeVideos/<videoId>/
 </ol>

 <hr>

 ## Strategy used

<hr>

#### Bachground Task
 - We can use Thread/Celery for fetching Youtube videos list
 - I have given option for both. But, I have tested only Thread method
#### API
- I have used Django REST Framework for this
#### Background Task Algo
- I have implemented Async and Sync methods for this
- I am checking stored videos publish date and 
- if it does not have old videos 
- then go for it
- otherwise search for only new videos
- After we have fetched all old videos
- I reset the search query for latest videos
- then search for new videos 