const videoCardContainer = document.querySelector('.video-container');
const previousBtn = document.getElementsByClassName('btn')[0];
const nextBtn = document.getElementsByClassName('btn')[1];

let API_link = window.location.protocol+ '//' + window.location.host + '/api/youtubeVideos/';


/* urlParam = {
    search: undefined,
    ordering: undefined,
    publishedAfter: undefined,
    publishedBefore: undefined,
    page: undefined,
    pageSize: undefined
} */

let buildURL = new URLSearchParams();

function Fetch(API_link){
    fetch(API_link)
    .then(res => res.json())
    .then(data => {
        videoCardContainer.innerHTML = '';
        
        if(data.next != null){
            nextBtn.style.display = "block";
            nextBtn.setAttribute('onclick','Fetch("'+data.next+'")')
        }
        else{
            nextBtn.style.display = "none";
        }

        if(data.previous != null){
            previousBtn.style.display = "block";
            previousBtn.setAttribute('onclick','Fetch("'+data.previous+'")')
        }
        else{
            previousBtn.style.display = "none";
        }

        data.results.forEach(video_data => {
            makeVideoCard(video_data);
        })
    })
    .catch(err => console.log(err));
}

const makeVideoCard = (data) => {
    videoCardContainer.innerHTML += `
    <div class="video" onclick="location.href = 'https://youtube.com/watch?v=${data.videoId}'">
        <img src="${data.thumbnailURL}" class="thumbnail" alt="">
        <div class="content">
            <div class="info">
                <h4 class="title">${data.videoTitle}</h4>
                <p class="channel-name">${data.publishDatetime}</p>
            </div>
        </div>
    </div>
    `;
}

Fetch(API_link);



// search bar

const searchInput = document.querySelector('.search-bar');
const searchBtn = document.querySelector('.search-btn');

searchBtn.addEventListener('click', () => {
    if(searchInput.value.length){
        buildURL.set('search', searchInput.value);
        Fetch(API_link + '?' + buildURL.toString());
    }
    else{
        buildURL.delete('search');
        Fetch(API_link + '?' + buildURL.toString());
    }
})

// Sorting Filters

const ascPublish = document.querySelector('#ascPublish');
const descPublish = document.querySelector('#descPublish');

ascPublish.addEventListener('click', () => {
    buildURL.set('ordering', 'publishDatetime');
    descPublish.classList.remove('active');
    ascPublish.classList.add('active');
    Fetch(API_link + '?' + buildURL.toString());
})

descPublish.addEventListener('click', () => {
    buildURL.set('ordering', '-publishDatetime');
    ascPublish.classList.remove('active');
    descPublish.classList.add('active');
    Fetch(API_link + '?' + buildURL.toString());
})

// Publish Date time filter

const publishBefore = document.querySelector('#publishBefore');
const publishAfter = document.querySelector('#publishAfter');

publishBefore.addEventListener('input', () => {
    if(publishBefore.value.length){
        buildURL.set('publishedBefore', publishBefore.value + 'Z');
        Fetch(API_link + '?' + buildURL.toString());
    }
    else{
        buildURL.delete('publishedBefore');
        Fetch(API_link + '?' + buildURL.toString());
    }
})

publishAfter.addEventListener('input', () => {
    if(publishAfter.value.length){
        buildURL.set('publishedAfter', publishAfter.value + 'Z');
        Fetch(API_link + '?' + buildURL.toString());
    }
    else{
        buildURL.delete('publishedAfter');
        Fetch(API_link + '?' + buildURL.toString());
    }
})

// Navigation Pagination Bar JS

var btns = document.querySelectorAll('.btn');
var paginationWrapper = document.querySelector('.pagination-wrapper');
var bigDotContainer = document.querySelector('.big-dot-container');
var littleDot = document.querySelector('.little-dot');

for(var i = 0; i < btns.length; i++) {
  btns[i].addEventListener('click', btnClick);
}

function btnClick() {
  if(this.classList.contains('btn--prev')) {
    paginationWrapper.classList.add('transition-prev');
  } else {
    paginationWrapper.classList.add('transition-next');  
  }
  
  var timeout = setTimeout(cleanClasses, 500);
}

function cleanClasses() {
  if(paginationWrapper.classList.contains('transition-next')) {
    paginationWrapper.classList.remove('transition-next')
  } else if(paginationWrapper.classList.contains('transition-prev')) {
    paginationWrapper.classList.remove('transition-prev')
  }
}