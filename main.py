from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, InputRequired
import requests
from dotenv import load_dotenv,dotenv_values
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
Bootstrap(app)
db = SQLAlchemy(app)
MOVIE_DATABASE_API=os.getenv('MOVIE_DATABASE_API')
MOVIE_DATABASE_SEARCH_URL='https://api.themoviedb.org/3/search/movie'


headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzNzBmNWQ1MzY0MThjZWM4MTc5ZWU1M2MxYzVlMTg5YiIsInN1YiI6IjY1ZDc3NmI2NjA5NzUwMDE4NTI1ODZjZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.RndiMJrXLGKh97En9jo-OtmPlxdYInDgGD1-f8Kb0tY"
        }


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250),unique=True,nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(300), nullable=True)
    img_url = db.Column(db.String(500), nullable=False)


with app.app_context():
    db.create_all()


class EditForm(FlaskForm):
    new_rating = FloatField('Rating out of 10 e.g. 7.5', validators=[InputRequired()])
    new_review = StringField('Your review', validators=[InputRequired()])
    edit = SubmitField('Done')


class AddForm(FlaskForm):
    movie_title = StringField('Movie Title',validators=[InputRequired()])
    add = SubmitField('Add Movie')


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()

    for i in range(len(movies)):
        movies[i].ranking=len(movies)-i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit/<int:id>", methods=["POST", "GET"])
def edit(id):
    edit_form = EditForm()
    if request.method == "POST" and edit_form.validate_on_submit():
        movie = Movie.query.get(id)
        movie.rating = request.form['new_rating']
        movie.review = request.form['new_review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form)


@app.route('/delete/<int:id>')
def delete(id):
    movie_to_delete = Movie.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add',methods=["POST","GET"])
def add():
    add_form = AddForm()
    if request.method=="POST" and add_form.validate_on_submit():

        response = requests.get(MOVIE_DATABASE_SEARCH_URL+f"?query={request.form['movie_title']}",headers=headers)
        movies=response.json()['results']
        return render_template('select.html',movies=movies)

    return render_template('add.html',form=add_form)


@app.route('/select/<int:movie_id>',methods=["GET"])
def select(movie_id):
    response=requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}',headers=headers)
    movie_data=response.json()
    movie_title=movie_data['original_title']
    movie_to_be_added=Movie(title=movie_title,img_url="https://image.tmdb.org/t/p/w500/"+movie_data['poster_path'],description=movie_data['overview'],year=movie_data['release_date'])
    db.session.add(movie_to_be_added)
    db.session.commit()
    movie_to_edit=Movie.query.filter_by(title=f"{movie_title}").first()
    return redirect(url_for('edit',id=movie_to_edit.id))


if __name__ == '__main__':
    app.run(debug=True)
