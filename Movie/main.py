import numpy as np
import pandas as pd
import re
from flask import Flask, render_template, request, redirect, session
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from nltk.stem.snowball import SnowballStemmer
import http.client
import pymysql
from tmdbv3api import Movie
from tmdbv3api import TMDb
from unidecode import unidecode
import os
import bs4 as bs
from urllib.request import Request, urlopen


app = Flask(__name__)
app.secret_key=os.urandom(24)

database = pymysql.connect(host="localhost",user="root",password="",database="movie") #Localhost Database connection.
cursor = database.cursor()

#Web application Database connection.
# database = pymysql.connect(host="maithrisharma.mysql.pythonanywhere-services.com",user="maithrisharma",password="pass",database="maithrisharma$Movie")
# cursor = database.cursor()


conn = http.client.HTTPSConnection("api.themoviedb.org")
payload = ''
headers = {}

tmdb = TMDb()
tmdb.api_key = '2d71ac9f8f76e2fe996cdc92cab9f9cd'

tmdb_movie = Movie()

#Home Page Template
@app.route("/home")
def home():

    if 'user_id' in session:
        return render_template('home.html')

    else:
        return redirect('/')

#Login Page Template
@app.route("/")
def login():

    return render_template('login.html')

#Register page Template
@app.route("/register")
def register():

    return render_template('register.html')


#Regex for Email Verfication
def isValidEmail(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (re.fullmatch(regex, email)):
        return True
    else:
        return False


#Password Validation
def isValidPassword(password):
    if len(password) < 8:
        res="Make sure your password is at least 8 letters"
    elif re.search('[0-9]', password) is None:
        res= "Make sure your password has a number in it"
    elif re.search('[A-Z]', password) is None:
        res= "Make sure your password has a capital letter in it"
    else:
        res="Proceed"

    return res


#Method for Login Validation
@app.route('/login_validation',methods=['POST','GET'])
def login_validation():
    email = request.form.get('email').lower()
    password = request.form.get('password')
    database = pymysql.connect(host="localhost",user="root",password="",database="movie")
    cursor = database.cursor()
    cursor.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""".format(email,password))
    user = cursor.fetchall()
    if len(user)>0:
            session['user_id']=user[0][0]
            session['user']=user[0][1]
            print(session['user_id'])
            print(session['user'])
            return redirect('/home')
    else:
        return render_template('login.html',error="Invalid Credentials")




#Method for Registering a New User into database.
@app.route('/register_user',methods=['POST','GET'])
def register_user():
    errorEmail=""
    fullName=request.form.get('ufullName')
    email=request.form.get('uemail').lower()
    password=request.form.get('upassword')
    errorPassword = isValidPassword(password)
    if not isValidEmail(email):
        errorEmail="Invalid Email."
    if errorPassword!="Proceed":
        errorPass=errorPassword
    else:
        database = pymysql.connect(host="localhost",user="root",password="",database="movie")
        cursor = database.cursor()
        cursor.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}'""".format(email))
        user = cursor.fetchall()
        if len(user) > 0:
            errorExists="Email already exists. Please use a different email."
            return render_template('register.html',errorExists=errorExists)
        else:
            cursor.execute("""INSERT INTO `users` (`userId`,`fullName`, `email`, `password`) VALUES (NULL,'{}','{}','{}')""".format(fullName,email,password))
            database.commit()
            cursor.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}'""".format(email))
            user=cursor.fetchall()
            session['user_id']=user[0][0]
            session['user'] = user[0][1]
            return redirect('/home')
    return render_template('register.html',errorEmail=errorEmail,errorPassword=errorPass)



#Logout method
@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id')

    return redirect('/')


#Method to Insert feedback for the Description Based Model
@app.route('/feedback',methods=['POST','GET'])
def feedback():
    if 'user_id' not in session:
        return redirect('/')

    else:
        id=session['user_id']
        title=request.form.get('title')
        if "'" in title:
            title=title.replace("'","''")
        rating=request.form.get('rating')
        if int(rating)<1 or int(rating)>5:
            rating=5
        message=request.form.get('message')
        if "'" in message:
            message=message.replace("'","''")
        database = pymysql.connect(host="localhost",user="root",password="",database="movie")
        cursor = database.cursor()

        cursor.execute("SELECT * from feedback where userId like %s AND title like %s",(id,title))
        userRating = cursor.fetchall()

        if len(userRating) > 0:
            ratingRes="Sorry! You've already rated for this movie recommendations"
        else:

            database = pymysql.connect(host="localhost",user="root",password="",database="movie")
            cursor = database.cursor()
            cursor.execute("INSERT INTO feedback(ratingId,userId,title,rating,message) VALUES(NULL,'{}','{}','{}','{}');".format(id,title,rating,message))
            database.commit()
            print("Inserted")
            ratingRes="Rating Submitted"

        return ratingRes


#Method to insert feedback for the Metadata based model
@app.route('/feedbackMeta',methods=['POST','GET'])
def feedbackMetadata():
    if 'user_id' not in session:
        return redirect('/')

    else:
        id=session['user_id']
        title=request.form.get('title')
        if "'" in title:
            title=title.replace("'","''")
        rating=request.form.get('rating')
        if int(rating)<1 or int(rating)>5:
            rating=5
        message=request.form.get('message')
        if "'" in message:
            message=message.replace("'","''")
        print(message)

        database = pymysql.connect(host="localhost",user="root",password="",database="movie")
        cursor = database.cursor()
        cursor.execute("""SELECT * FROM `feedbackmetadata` WHERE `userId` LIKE '{}' AND `title` LIKE '{}'""".format(id,title))
        userRating = cursor.fetchall()

        if len(userRating) > 0:
            ratingRes="Sorry! You've already rated for this movie recommendations"
        else:
            #print("Inside Else")
            database = pymysql.connect(host="localhost",user="root",password="",database="movie")
            cursor = database.cursor()
            cursor.execute("INSERT INTO feedbackmetadata(ratingId,userId,title,rating,message) VALUES(NULL,'{}','{}','{}','{}');".format(id,title,rating,message))
            database.commit()
            print("Inserted")
            ratingRes="Rating Submitted"

        return ratingRes


#Gathering the Movie Title and id from the JS and calling the descriptionrcmd method
@app.route("/descriptionSimilarity",methods=["POST"])
def descriptionSimilarity():
    if 'user_id' not in session:
        return redirect('/')

    else:
        movie = request.form['movie']
        id = request.form['id']
        rc = descriptionrcmd(movie,id)
        print(rc)
        # print(similary_scores)
        if type(rc)==type('string'):
            return rc
        else:
            m_str="---".join(rc)
            final_str = m_str

            print(final_str)
            return m_str

#Gathering the movie title and id from the JS and calling metadatarcmd method
@app.route("/metadataSimilarity",methods=["POST"])
def metadataSimilarity():
    if 'user_id' not in session:
        return redirect('/')

    else:
        movie = request.form['movie']
        id = request.form['id']
        rc = metadatarcmd(movie,id)
        print(rc)
        if type(rc)==type('string'):
            return rc
        else:
            m_str="---".join(rc)

            final_str = m_str

            print(final_str)
            return m_str


#Method to load Description HTML
@app.route('/description')
def description_ui():
    if 'user_id' in session:
        data = pd.read_csv('descfinal_data.csv')
        l = list(data['title'].str.capitalize())
        return render_template("description.html")

    else:
        return redirect('/')


#Method to laod Metadata HTML
@app.route('/metadata')
def metadata_ui():
    if 'user_id' in session:
        data = pd.read_csv('final_data.csv')
        l = list(data['title'].str.capitalize())
        return render_template("metadata.html")

    else:
        return redirect('/')



#Method to prepare all gathered detailed movie information from the API
@app.route("/description_movies", methods=["GET","POST"])
def recommendDescription():

    if 'user_id' not in session:
        return redirect('/')

    else:
        # getting data from AJAX request
        title = request.form['title']
        id = request.form['id']

        poster = request.form['poster']
        genres = request.form['genres']
        overview = request.form['overview']
        vote_average = request.form['rating']
        vote_count = request.form['vote_count']
        release_date = request.form['release_date']
        runtime = request.form['runtime']
        status = request.form['status']
        rec_movies = request.form['movies']
        rec_posters = request.form['movieposters']

        rec_movies = listConvert(rec_movies)
        rec_posters = listConvert(rec_posters)

        movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}

        #Web scraping the watch providers information
        soup_title = title.lower()
        if "\'" in soup_title:
            soup_title = soup_title.replace("'", "-")
        soup_title = soup_title.split(" ")
        soup_title="-".join(soup_title)

        #Location is set to UK
        link="https://www.themoviedb.org/movie/"+id+"-"+soup_title+"/watch?locale=GB"
        #link=link.encode('utf-8')
        link=unidecode(link)
        print(link)
        req = Request(link, headers={'User-Agent': 'Mozilla/5.0'})

        web_byte = urlopen(req).read()

        source = web_byte.decode('utf-8')

        soup = bs.BeautifulSoup(source, 'html.parser')
        divs = soup.find_all('div', class_='ott_provider')
        lis = soup.find_all('li', class_='ott_filter_best_price')
        # watch_providers=[]
        s=[]
        for i in divs:

            s.append(str(i))
        watch_providers = ''.join(s)
        watch_providers= watch_providers.replace(" src=\"/t/p/original",r' src="/static')
        watch_providers = watch_providers.replace("$", "£")

        #Rendering the DescriptionBased Template that shows Detailed Movie information,
        #Watch providers information and top 15 movies with its posters.
        return render_template('descriptionBased.html', title=title, poster=poster, overview=overview, vote_average=vote_average,
                               vote_count=vote_count, release_date=release_date, runtime=runtime, status=status,
                               genres=genres,
                               movie_cards=movie_cards,watch_providers = watch_providers)



#Method to prepare all gathered detailed movie information from the API
@app.route("/metadata_movies", methods=["GET","POST"])
def recommendMetadata():
    if 'user_id' not in session:
        return redirect('/')

    else:
        # getting data from AJAX request
        title = request.form['title']
        id = request.form['id']

        poster = request.form['poster']
        genres = request.form['genres']
        overview = request.form['overview']
        vote_average = request.form['rating']
        vote_count = request.form['vote_count']
        release_date = request.form['release_date']
        runtime = request.form['runtime']
        status = request.form['status']
        rec_movies = request.form['movies']
        rec_posters = request.form['movieposters']


        rec_movies = listConvert(rec_movies)
        rec_posters = listConvert(rec_posters)

        movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}

        # Web scraping the watch providers information
        soup_title = title.lower()
        if "\'" in soup_title:
            soup_title = soup_title.replace("'", "-")
        soup_title = soup_title.split(" ")
        soup_title="-".join(soup_title)
        # Location is set to UK
        link="https://www.themoviedb.org/movie/"+id+"-"+soup_title+"/watch?locale=GB"
        link = unidecode(link)
        print(link)

        req = Request(link, headers={'User-Agent': 'Mozilla/5.0'})
        web_byte = urlopen(req).read()
        source = web_byte.decode('utf-8')
        #source = urllib.request.urlopen(link).read()

        soup = bs.BeautifulSoup(source, 'html.parser')
        divs = soup.find_all('div', class_='ott_provider')
        lis = soup.find_all('li', class_='ott_filter_best_price')
        # watch_providers=[]
        s=[]
        for i in divs:

            s.append(str(i))

        watch_providers = ''.join(s)
        watch_providers= watch_providers.replace(" src=\"/t/p/original",r' src="/static')
        watch_providers = watch_providers.replace("$","£")

        # Rendering the metadataBased Template that shows Detailed Movie information,
        # Watch providers information and top 15 movies with its posters.
        return render_template('metadataBased.html', title=title, poster=poster, overview=overview, vote_average=vote_average,
                               vote_count=vote_count, release_date=release_date, runtime=runtime, status=status,
                               genres=genres,
                               movie_cards=movie_cards,watch_providers = watch_providers)




#Method to read the CSV file and create similarity matrix using CountVectorizer for Metadata based model
def metadata_similarity():
    data = pd.read_csv('final_data.csv')
    cv = CountVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
    count_matrix = cv.fit_transform(data['comb'].values.astype('U'))
    similarity = cosine_similarity(count_matrix)
    return data,similarity

#Method to read the CSV file and create similarity matrix using TfidfVectorizer for Description based model
def description_similarity():
    data = pd.read_csv('descfinal_data.csv')
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(data['comb'].values.astype('U'))
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    return data,cosine_sim



#Method to get Genres for the searched movie if not present in the database
def get_genre(id):
    genres = []

    movie_details = tmdb_movie.details(id)
    movie_genres = movie_details.genres
    if movie_genres:
        genre_str = " "
        for i in range(0, len(movie_genres)):
            genres.append(movie_genres[i]['name'])
        return genre_str.join(genres)
    else:
        return np.NaN


#Method to get Keywords for the searched movie if not present in the database
def get_keywords(id):
    keywords = []

    movie_keywords = tmdb_movie.keywords(id)
    movie_keywords = movie_keywords['keywords']
    stemmer = SnowballStemmer('english')
    if movie_keywords:

        for i in range(0, len(movie_keywords)):
            n = movie_keywords[i]['name']
            if ', ' in n:
                m = n.split(', ')
                #print(m)
                for j in m:
                    keywords.append(stemmer.stem(j))
            else:

                keywords.append(stemmer.stem(n))

        return ' '.join(keywords)
    else:
        return np.NaN

#Method to get Cast and Crew for the searched movie if not present in the database
def get_cast(id):
    cast = []
    director = ""
    movie_credits = tmdb_movie.credits(id)
    if movie_credits['cast'] and movie_credits['crew']:
        for i in movie_credits['crew']:
            if i.get('job') == 'Director':
                director = i.get('name').lower().replace(" ", "")
                break
        if len(movie_credits['cast'])>=3:
            for i in range(0, 3):
                c = movie_credits['cast'][i]['name'].lower().replace(" ", "")
                cast.append(c)
        elif len(movie_credits['cast'])==2:
            for i in range(0, 2):
                c = movie_credits['cast'][i]['name'].lower().replace(" ", "")
                cast.append(c)
            cast.append(" ")
        elif len(movie_credits['cast'])==1:
            c = movie_credits['cast'][0]['name'].lower().replace(" ", "")
            cast.append(c)
            cast.append(" ")
            cast.append(" ")
        return cast, director
    else:
        return np.NaN,np.NaN


#Method to insert new row into database if the searched movie is not present and calling the similarity method.
# This method also sorts the similar movie to the top 15.
def metadatarcmd(m,id):
    print("Inside metadatarcmd")
    if 'user_id' not in session:
        return redirect('/')

    else:
        id = int(id)
        m = m.lower()
        data = pd.read_csv('final_data.csv')
        id_list = list(data['id'])
        id_list = [ int(x) for x in id_list]
        if id not in id_list:
            new_row = {
                'id':id,
                'director': "",
                'actor1': "",
                'actor2': "",
                'actor3': "",
                'genres':"",
                'keywords':"",
                'title':m,
                'comb': ""
            }
            new_row['genres']=str(get_genre(id))
            new_row['keywords']=str(get_keywords(id))
            cast_list,new_row['director'] = get_cast(id)
            new_row['actor1'] = str(cast_list[0])
            new_row['actor2'] = str(cast_list[1])
            new_row['actor3'] = str(cast_list[2])
            new_row['comb'] = new_row['genres'] + ' ' + new_row['keywords'] + ' '+ new_row['actor1'] + ' '+ new_row['actor2'] +' ' + new_row['actor3'] +' ' + new_row['director']
            df= pd.DataFrame(pd.Series(new_row)).T

            # append data frame to CSV file
            df.to_csv('final_data.csv', mode='a', index=False, header=False)
            print("Data appended successfully.")


        data, similarity = metadata_similarity()
        i = data.loc[data['id'] == id].index[0]
        lst = list(enumerate(similarity[i]))

        lst = sorted(lst, key=lambda x: x[1], reverse=True)

        lst = lst[1:16]
        print(lst)
        l = []
        sim_scores = []
        for i in range(len(lst)):
            a = lst[i][0]
            sm = lst[i][1] * 100
            sm = round(sm, 2)
                # data.loc[data.country == 'Italy']
                #print(l.append(data['title'][a]))
            l.append(data['title'][a])

            sim_scores.append(sm)
        sim_scores = list(map(str, sim_scores))
        return l


#Method to get Description information of the searched movie if not present in the database.
def get_description(id):
    # description = ""

    movie_details = tmdb_movie.details(id)
    if movie_details['overview'] and movie_details['tagline']:
        return movie_details['overview'] + "@@@" + movie_details['tagline']
    elif movie_details['overview'] and not movie_details['tagline']:
        return movie_details['overview'] + "@@@" + ""
    elif not movie_details['overview'] and movie_details['tagline']:
        return "" + "@@@" + movie_details['tagline']
    else:
        return "@@@"




#Method to insert new row into database if the searched movie is not present and calling the similarity method.
# This method also sorts the similar movie to the top 15.
def descriptionrcmd(movie, id):
    if 'user_id' not in session:
        return redirect('/')

    else:

        id=int(id)
        m = movie.lower()
        data = pd.read_csv('descfinal_data.csv')
        id_list = list(data['id'])
        id_list = [int(x) for x in id_list]
        if id not in id_list:
            new_row = {
                'id':id,
                'overview': "",
                'tagline': "",
                'title': m,
                'comb': ""
            }
            temp = get_description(id)
            temp=temp.split("@@@")
            new_row['overview'] = temp[0]
            new_row['tagline'] = temp[1]
            new_row['comb'] = str(new_row['overview']) + ' ' + str(new_row['tagline'])
            df = pd.DataFrame(pd.Series(new_row)).T

            # append data frame to CSV file
            df.to_csv('descfinal_data.csv', mode='a', index=False, header=False)
            print("Data appended successfully.")


        data, similarity = description_similarity()
        i = data.loc[data['id'] == id].index[0]
        lst = list(enumerate(similarity[i]))
        #print(lst)
        lst = sorted(lst, key=lambda x: x[1], reverse=True)

        lst = lst[1:16]
        print(lst)
        l = []
        sim_scores = []
        for i in range(len(lst)):
            a = lst[i][0]
            sm = lst[i][1] * 100
            sm = round(sm, 2)
            l.append(data['title'][a])

            sim_scores.append(sm)
        sim_scores = list(map(str, sim_scores))
        return l




#Method to convert list
def listConvert(li):
    li = li.split('","')
    li[0] = li[0].replace('["','')
    li[-1] = li[-1].replace('"]','')
    return li


if __name__=='__main__':
    app.run(debug=True)
