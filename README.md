<img src="https://externship.github.in/assets/Logo/Logo%20Color.svg" height="110"><img src="https://externship.github.in/assets/org-logos/Fampay.png" align ="right" height="110">


# GithubExternship Fampay Backend Assignment
To make an API to fetch latest videos sorted in reverse chronological order of their publishing date-time from YouTube for a given tag/search query in a paginated response.

<hr>

### 🗒 Problem Statement
<details>
  <summary>Click to expand</summary>
   
### Basic Requirements:

- [x] Server should call the YouTube API continuously in background (async) with some interval (say 10 seconds) for fetching the latest videos for a predefined search query and should store the data of videos (specifically these fields - Video title, description, publishing datetime, thumbnails URLs and any other fields you require) in a database with proper indexes.

- [x] A GET API which returns the stored video data in a paginated response sorted in descending order of published datetime.

- [x] It should be scalable and optimized.

### Bonus Points:

- [x] Add support for supplying multiple API keys so that if quota is exhausted on one, it automatically uses the next available key.

- [x] Make a dashboard to view the stored videos with filters and sorting options (optional)

### Instructions:
* You are free to choose any search query, for example: official, cricket, football etc. (choose something that has high frequency of video uploads)
* Try and keep your commit messages clean, and leave comments explaining what you are doing wherever it makes sense.
* Also try and use meaningful variable/function names, and maintain indentation and code style.
* Submission should have a README file containing instructions to run the server and test the API.
* Submission should be done on GitHub Externship Portal.


### Reference:
* [YouTube data v3 API](https://developers.google.com/youtube/v3/getting-started)
* [Search API reference](https://developers.google.com/youtube/v3/docs/search/list)
* To fetch the latest videos you need to specify these: type=video, order=date, publishedAfter=<SOME_DATE_TIME>
Without publishedAfter, it will give you cached results which will be too old
</details>

<hr>
   
### 🎰 Instruction for running the project
   
<details>
  <summary>Click to expand
     
   Try it Now! Just go to Deployment 👇</summary>
<ul>
   <li>Set environment variable <code>DEVELOPER_KEY</code> with one or more API keys separated by white space e.g. API_KEY_1 API_KEY_2</li> 
</ul>
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

   As it is browsable API, so we can access it through browser using same link and it support `page`, `pageSize`, `search`, `ordering`, `publishedAfter` & `publishedBefore` query parameters.

   Also, We can access specific video details by using its videoId like following
   
    http://127.0.0.1:8000/api/youtubeVideos/<videoId>/
   
   **For Accessing Dashbord**
   
    http://127.0.0.1:8000/
 </ol>
 </details>
 <hr>
   
 ### 🚀 Deployment
   
 - Deployed on ![Microsoft Azure](https://img.shields.io/badge/Microsoft_Azure-232F7E?style=flat-square&logo=microsoft-azure&logoColor=white)
 - Dashboard Link: https://scrib1.azurewebsites.net/
 - API Link: https://scrib1.azurewebsites.net/api/youtubeVideos/
   
 <hr>
   
 ### 🛠 Tech Stack
  ![python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=Python&logoColor=white)
  ![Django](https://img.shields.io/badge/-Django-092E20?style=for-the-badge&logo=Django&logoColor=white)
  ![Django REST Framework](https://img.shields.io/badge/-Django_REST_Framework-8f3900?style=for-the-badge&logo=Django&logoColor=white)
  ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=for-the-badge&logo=SQLite&logoColor=white)
  ![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
  ![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
  ![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=JavaScript&logoColor=black)
   
 `Note:` For low cost deployment I have used SQLite. This Web-app is compatible with PostgreSQL, MariaDB, MySQL, Oracle [ Thanks to Django ORM :) ]
   
 <hr>

 ## 🎯 Strategy used
   
#### Highlights of Algorithm
- `In one cycle only 1 API call and 1 Database query`
- In worse case [ Happens only once at app start ] only 1 API call and 3 Database query [ It's not bug, it's part of algorithm ]
- If this app is deployed on `single core & single thread` hardware, it will still give good performnce due to its `Async Background Task Function`
- Auto wait for API key's quota reset

<details>
  <summary>Know More about Algorithm</summary>
  
#### Bachground Task Options
 - We can use Thread/Celery for fetching Youtube videos list
 - I have given option for both. But, I have tested only Thread method
 - I have implemented Async and Sync both functions for this task. We can choose any one
#### Background Task Algorithm
- As Django App was booting, we will wait for 10 seconds to boot it completely
- Then fetching the earliest and latest publish dates from local database
- Checking fetched publish date:
   ```
   if local database does not have old videos [ Videos from assumed earliest date ] 

   then fetched all remaining old videos [ After that, search query is rebuild for latest videos ]

   otherwise search for only new video
   ```
- If in process, API key's quota exceeded. Then wait for it's quota reset. After reset, process will again continue.

> For More Verbose Algorithm checkout comments of [`scrib/tasks.py`](https://github.com/AbhishekMore-1/GithubExternship-Fampay-Backend/blob/main/scrib/tasks.py)

</details>
<hr>
  
## 😎 Challenges vs Hacks
  
<table>
  <thead align="center">
    <tr>
      <td><strong>Challenges</strong></td>
      <td><strong>Hacks</strong></td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Background Task Algorithm</td>
      <td>Note down all scenario [ Same video in API response ]<br>
      Find simple flow<br>
      Optimise flow [ Minimise DB query & API call ]</td>
    </tr>
    <tr>
      <td>Async version of background task</td>
      <td>Used asyncio & aiohttp for async Youtube Data API call<br>
      Craft general API url string</td>
    </tr>
    <tr>
      <td>Async database query</td>
      <td>Used sync_to_async function from asgiref.sync<br>
      Custom function for filter query</td>
    </tr>
  </tbody>
 </table>

> For Complete Journey of Challenges Vs Hacks, checkout [`comments of commits`](https://github.com/AbhishekMore-1/GithubExternship-Fampay-Backend/commits/main)
