var movie_title;
var ratedIndex;
$(function() {

// Button will be disabled until we type anything inside the input field
  document.getElementById('movieSearch').addEventListener('input', function(e) {
    if(e.target.value==""){
      document.getElementById('search').disabled = true;
    }
    else{
      document.getElementById('search').disabled = false;
    }
  });

//Search Event on click
  $("#search").click(function(){
    var title = document.getElementById("movieSearch").value;
    console.log(title);
    var api_key = "2d71ac9f8f76e2fe996cdc92cab9f9cd";
    if(title!=""){
        searchMovie(api_key,title);
    }
  });

});

//Saving the Ratings to the database using AJAX
function saveRating(ratedIndex){
    var message = document.getElementById("message").value;
    console.log(message);
    console.log(ratedIndex);
    $.ajax({
        type : 'POST',
        url : '/feedbackMeta',
        data:{'title':movie_title,'rating':ratedIndex,'message':message},
        success: function(ratingRes){
        //console.log(ratingRes)
        if(ratingRes=="Sorry! You've already rated for this movie recommendations"){
            alert("Sorry! You've already rated!");
            //Redirect to the Home Page
            window.setTimeout(function(){window.location.href = 'home';},1000);
      }
      else {
        alert("Rating Submitted");
        //console.log(ratedIndex);
        //Redirect to the Home Page
        window.setTimeout(function(){window.location.href = 'home';},1000);
        }


    },
    error: function(){
      alert("Try Again");
    },
    });
}

//Search if the Movie is present in TMDB
function searchMovie(api_key,title){
  $.ajax({
    type: 'GET',
    url:'https://api.themoviedb.org/3/search/movie?api_key='+api_key+'&query='+title,

    success: function(movie){
    //If no movies found with the searched title display the error message
      if(movie.results.length<1){
        $('.error').css('display','block');
        $('.success').css('display','none');
        $(".loader").delay(500).fadeOut();

      }
      else{
      $(".loader").fadeIn();
        $('.success').delay(1000).css('display','block');
        var movie_id = movie.results[0].id;
        if(movie.results[0].original_language!="en"){
        //If the original language is not English, keep the title to english title
            movie_title = movie.results[0].title;
        }

        else{
        //Else change the title to Original Title
            movie_title = movie.results[0].original_title;
        }

        getRecommendations(movie_title,movie_id,api_key);
      }
    },
    error: function(){
      alert('Invalid Request');
      $(".loader").delay(500).fadeOut();
    },
  });
}
//Gathering Similar Movies from the database by using AJAX
function getRecommendations(movie_title,movie_id,api_key){
  $.ajax({
    type:'POST',
    url:"/metadataSimilarity",
    data:{'movie':movie_title,'id':movie_id},
    success: function(recs){
      if(recs=="Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies"){
        $('.error').css('display','block');
        $('.success').css('display','none');
         $(".loader").delay(500).fadeOut();
      }
      else {
        $('.error').css('display','none');
        $('.success').css('display','block');
        var movie_arr = recs.split('---');
        var arr = [];
        for(const movie in movie_arr){
          arr.push(movie_arr[movie]);
        }
        //Function to gather detailed movie information
        getDetails(movie_id,api_key,arr,movie_title);
      }
    },
    error: function(){
          //Display alert if there is any API error
      alert("error recommendations");
      $(".loader").delay(500).fadeOut();
    },
  });
}
//Gather Detailed Movie information
function getDetails(movie_id,api_key,arr,movie_title) {
  $.ajax({
    type:'GET',
    url:'https://api.themoviedb.org/3/movie/'+movie_id+'?api_key='+api_key,
    success: function(movie_details){
    //Function to display detailed movie information
      displayMovie(movie_details,arr,movie_title,api_key,movie_id);
    },
    error: function(){
      alert("API Error!");
      $(".loader").delay(500).fadeOut();
    },
  });
}

//Function to display detailed movie information
function displayMovie(movie_details,arr,movie_title,api_key,movie_id){
  var poster = 'https://image.tmdb.org/t/p/original'+movie_details.poster_path;
  var overview = movie_details.overview;
  var genres = movie_details.genres;
  var rating = movie_details.vote_average;
  var vote_count = movie_details.vote_count;
  var release_date = new Date(movie_details.release_date);
  var runtime = parseInt(movie_details.runtime);
  var status = movie_details.status;
  var genre_list = []
  for (var genre in genres){
    genre_list.push(genres[genre].name);
  }
  var my_genre = genre_list.join(", ");
  if(runtime%60==0){
    runtime = Math.floor(runtime/60)+" hour(s)"
  }
  else {
    runtime = Math.floor(runtime/60)+" hour(s) "+(runtime%60)+" min(s)"
  }
  //Collect Movie posters for all 15 similar movies
  movieposters = posters(arr,api_key);

  details = {
   'title':movie_title,
    'id':movie_id,
      'poster':poster,
      'genres':my_genre,
      'overview':overview,
      'rating':rating,
      'vote_count':vote_count.toLocaleString(),
      'release_date':release_date.toDateString().split(' ').slice(1).join(' '),
      'runtime':runtime,
      'status':status,
      'movies':JSON.stringify(arr),
      'movieposters':JSON.stringify(movieposters),
  }

//Posting to the python method using AJAX that sends the information to the HTML
  $.ajax({
    type:'POST',
    data:details,
    url:"/metadata_movies",
    dataType: 'html',
    complete: function(){
      $(".loader").delay(500).fadeOut();
    },

    success: function(response) {
      $('.success').html(response);
      $(window).scrollTop(0);
       $('#feedbackbtnMeta').on('click',function(){
   // console.log("Second Feedback");
    saveRating(ratedIndex);
    //console.log("Second feedback out");
    });
    },
    error: function(){
      alert("API Error!");
    },
  });
}
//Gathering posters of the 15 movies from the TMDB
function posters(arr,api_key){
  var moviePosters = []
  for(var m in arr) {
    $.ajax({
      type:'GET',
      url:'https://api.themoviedb.org/3/search/movie?api_key='+api_key+'&query='+arr[m],
      async: false,
      success: function(movieData){
        moviePosters.push('https://image.tmdb.org/t/p/original'+movieData.results[0].poster_path);
      },
      error: function(){
      $(".loader").delay(500).fadeOut();
        alert("Invalid Request!");
      },
    })
  }
  return moviePosters;
}

//When clicked on similar movie cards, the selected movie information is displayed
function movieCard(e){
  var api_key = '2d71ac9f8f76e2fe996cdc92cab9f9cd';
  var title = e.getAttribute('title');
  searchMovie(api_key,title);

}

//Document on scroll function
$(document).scroll(function () {
    var y = $(this).scrollTop();
    //If the page is scrolled till the similar movies information, the rating forms pops up
    if (y > 800) {
        $('#myForm').fadeIn();
    } else {
        $('#myForm').fadeOut();
    }
    ratedIndex =-1;
    //On click on the stars
  $('.fa-star').on('click',function(){
    ratedIndex = parseInt($(this).data('index'))+1;
    console.log(ratedIndex);

  });
  //On Hover, the stars are filled with Yellow color
  $('.fa-star').mouseover(function (){
    resetStarColors();
    var ci = parseInt($(this).data('index'));
    for(var i=0;i<=ci;i++){
        $('.fa-star:eq('+i+')').css('color','yellow');
    }
  });
  //When the mouse is left, the stars are filled till the selected star
    $('.fa-star').mouseleave(function (){
        resetStarColors();

        if(ratedIndex!=-1){
            for(var i=0;i<ratedIndex;i++){
                $('.fa-star:eq('+i+')').css('color','yellow');
            }
        }
    });
    //Reset the star colors
    function resetStarColors(){
        $('.fa-star').css('color','white');
    }

});