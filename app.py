#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import timezone
import json
import sys
import dateutil.parser
import babel
#from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask import (
  Flask,
  render_template,
  request,
  flash,
  redirect,
  url_for
)

from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import collate
from forms import *
from flask_migrate import Migrate
from models import app, db, Venue, Artist, Shows
#from config import DatabaseURI
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

#app = Flask(__name__)
moment = Moment(app)
#app.config.from_object(DatabaseURI)
app.config.from_object('config')
db.init_app(app)
#db = SQLAlchemy(app)
#migrate = Migrate(app, db)







#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = Venue.query.order_by(Venue.created_date.desc()).limit(3).all()
  artists = Artist.query.order_by(Artist.created_date.desc()).limit(3).all()

  venue = []
  for venuess in venues:
    venue.append({
      "id": venuess.id,
      "name": venuess.name,
      "city": venuess.city
    })
  artist = []
  for artistss in artists:
    artist.append({
      'id': artistss.id,
      'name': artistss.name,
      'city': artistss.city
    })

  return render_template('pages/home.html', venues=venue, artists=artist)
  #return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  venues = Venue.query.distinct(Venue.city, Venue.state).all()
  data = []
  for check in venues:
    result ={
      'city': check.city,
      'state': check.state
    }
    venue_name = Venue.query.filter_by(city=check.city, state=check.state).all()
    collate_venue = []
    for check_venue in venue_name:
      collate_venue.append({       
        'id': check_venue.id,
       'name': check_venue.name,       
      })

      result['venues'] = collate_venue
      data.append(result)
    
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  text = request.form.get("search_term")
  #search = Artist.query.filter(Artist.name == text).all()
  search = Venue.query.filter(Venue.name.ilike(f'%{text}%')).all()
  
  search_result = {
    'count':len(search),
    'data': []
  }

  for searching in search:
    search_result['data'].append({
      'id':searching.id,
      'name':searching.name
    })

  db.session.close()

  return render_template('pages/search_venues.html', results= search_result, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    upcoming_shows = db.session.query(Shows).join(Venue).filter(Shows.venue_id == venue_id).filter(Shows.show_time >= db.func.now())
    prev_shows = db.session.query(Shows).join(Venue).filter(Shows.venue_id == venue_id).filter(Shows.show_time < db.func.now())
     
    upcoming = []
    previous = []

    for shows in upcoming_shows:
      upcoming.append({
        'start_time' : str(shows.show_time.strftime('%Y-%m-%d %H:%M:%S')),
        'artist_image_link': shows.artist.image_link,
        'artist_name': shows.artist.name,
        'artist_id': shows.artist.id
      })

    for shows in prev_shows:
      previous.append({
        'start_time' : str(shows.show_time.strftime('%Y-%m-%d %H:%M:%S')),
        'artist_image_link': shows.artist.image_link,
        'artist_name': shows.artist.name,
        'artist_id': shows.artist.id

      })
    upcoming_count = len(upcoming)
    prev_count =len(previous)
    data = {
      'upcoming_shows_count': upcoming_count, 
      'past_shows_count': prev_count,
      'upcoming_shows': upcoming,
      'past_shows':previous
      }
    return render_template("pages/show_venue.html", data=data, venue=venue)
  
  
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():


  

    form = VenueForm(request.form)
    if form.validate():
      try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        address = form.address.data
        phone = form.phone.data
        genres = form.genres.data
        fb_link = form.facebook_link.data
        website_link = form.website_link.data
        image_link = form.image_link.data
        seeking_talent = form.seeking_talent.data
        seeking_description = form.seeking_description.data
  
        new_venue = Venue(name = name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link= fb_link, website_link=website_link, image_link =image_link, seeking_description= seeking_description, seeking_talent=seeking_talent)
        db.session.add(new_venue)
        db.session.commit()
    # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

  #except:
      except:
        db.session.rollback()
        flash('Venue' + request.form['name'] + 'was not listed')
        print(sys.exc_info())
      finally:
        db.session.close()
        return render_template('pages/home.html')
    else:
      flash('Form input invalid')
      for field, message in form.errors.items():
        #flash(field + ' - ' + str(message))
        flash(str(message))
        return render_template('pages/home.html')



@app.route('/venues/<int:venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)

  try:
    #Venue.query.filter_by(id=venue_id).delete()
    db.session.delete(venue)
    db.session.commit()
    flash('Venue deletion succesful')

  except:
    db.session.rollback()
    flash('Try deleting again')

  finally:
    db.session.close()
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template("pages/show_venue.html")

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  artist = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artist)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  text = request.form.get("search_term")
  #search = Artist.query.filter(Artist.name == text).all()
  search = Artist.query.filter(Artist.name.ilike(f'%{text}%')).all()
  
  search_result = {
    'count':len(search),
    'data': []
  }

  for searching in search:
    search_result['data'].append({
      'id':searching.id,
      'name':searching.name
    })

  db.session.close()
  return render_template('pages/search_artists.html', results = search_result , search_term=request.form.get('search_term', ''))
  

@app.route('/artists/<int:artist_id>', methods = ['GET'])
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  upcoming_shows = db.session.query(Shows).join(Artist).filter(Shows.artist_id == artist_id).filter(Shows.show_time >= db.func.now()).all()
  previous_shows = db.session.query(Shows).join(Artist).filter(Shows.artist_id == artist_id).filter(Shows.show_time < db.func.now()).all()


  upcoming = []
  previous = []
  for shows in upcoming_shows:
     upcoming.append({
       'start_time': str(shows.show_time.strftime('%Y -%m-%d %H:%M:S')),
       'venue_image_link': shows.venue.image_link,
       'venue_id' : shows.venue_id,
       'venue_name': shows.venue.name
     })

  for shows in previous_shows:
    previous.append({
      'start_time': str(shows.show_time.strftime('%Y -%m-%d %H:%M:S')),
       'venue_image_link': shows.venue.image_link,
       'venue_id' : shows.venue_id,
       'venue_name': shows.venue.name
    })
  upcoming_count = len(upcoming)
  previous_count = len(previous)
  data = {
    'upcoming_shows_count': upcoming_count,
    'past_shows_count': previous_count,
    'upcoming_shows': upcoming,
    'past_shows': previous
  }
  
  # shows the artist page with the given artist_id
 
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', data=data, artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  edit_artist = Artist.query.get(artist_id)
  form.name.default = edit_artist.name
  form.state.default = edit_artist.state
  form.city.default = edit_artist.city
  form.phone.default = edit_artist.phone
  form.website_link.default = edit_artist.website_link
  form.facebook_link.default = edit_artist.facebook_link
  form.seeking_venue.default = edit_artist.seeking_venue
  form.seeking_description.default = edit_artist.seeking_description
  form.genres.default = edit_artist.genres
  form.process()
  


  return render_template('forms/edit_artist.html', form=form, artist=edit_artist)

def Request(field):
  if field == 'genres':
    return request.form.getlist(field)
  elif field == 'seeking_talent' or field == 'seeking_venue' and request.form[field] == 'y':
    return True
  elif field == 'seeking_talent' or field == 'seeking_venue' and request.form[field] != 'y':
    return False
  else:
    return request.form[field]



@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  edited_artist = Artist.query.get(artist_id)
  try:  
    edited_artist.name = Request('name')
    edited_artist.genres = Request('genres')
    edited_artist.city = Request('city')
    edited_artist.phone = Request('phone')
    edited_artist.state = Request('state')
    edited_artist.website_link = Request('website_link')
    edited_artist.seeking_talent = Request('seeking_talent')
    edited_artist.seeking_description = Request('seeking_description')
    edited_artist.facebook_link = Request('facebook_link')
    edited_artist.image_link = Request('image_link')
    db.session.commit()
    flash('Artist ' + request.form['name'] + 'details has been succesfully updated!')
  except:
    flash('Error please try that again')
    db.session.rollback()

  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  edit_venue = Venue.query.get(venue_id)
  form.name.default = edit_venue.name
  form.state.default = edit_venue.state
  form.city.default = edit_venue.city
  form.phone.default = edit_venue.phone
  form.website_link.default = edit_venue.website_link
  form.facebook_link.default = edit_venue.facebook_link
  form.seeking_talent.default = edit_venue.seeking_talent
  form.seeking_description.default = edit_venue.seeking_description
  form.genres.default = edit_venue.genres
  form.address.default = edit_venue.address
  form.process()
  
  
  
  
  

  return render_template('forms/edit_venue.html', form=form, venue=edit_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  edited_venue = Venue.query.get(venue_id)
  try:  
    edited_venue.name = Request('name')
    edited_venue.genres = Request('genres')
    edited_venue.city = Request('city')
    edited_venue.phone = Request('phone')
    edited_venue.state = Request('state')
    edited_venue.website_link = Request('website_link')
    edited_venue.seeking_talent = Request('seeking_talent')
    edited_venue.seeking_description = Request('seeking_description')
    edited_venue.facebook_link = Request('facebook_link')
    edited_venue.image_link = Request('image_link')
    edited_venue.address = Request('address')
    db.session.commit()
    flash('Venue ' + request.form['name'] + 'details has been succesfully updated!')
  except:
    flash('Unsuccessful, try that again')
  
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    
    form = ArtistForm(request.form)
    #this block validates users input form
    if form.validate():
      try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        fb_link = form.facebook_link.data
        website_link = form.website_link.data
        image_link = form.image_link.data
        seeking_venue = form.seeking_venue.data
        seeking_description = form.seeking_description.data
    
        new_artist = Artist(name = name, city=city, state=state, phone=phone, genres=genres, facebook_link= fb_link, website_link=website_link, image_link =image_link, seeking_description= seeking_description, seeking_venue=seeking_venue)
        db.session.add(new_artist)
        db.session.commit()
    
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
      except:
        db.session.rollback()
        flash('Artist ' + request.form['name'] + ' was not listed')
        print(sys.exc_info())


      finally:
        db.session.close()
        return render_template('pages/home.html')
    
    else:
      flash('Form input invalid')
      for field, message in form.errors.items():
        #flash(field + ' - ' + str(message))
        flash(str(message))
        return render_template('pages/home.html')

#Yet to do the delete button
      


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  show = db.session.query(Shows).join(Artist).all()
  shows = []

  for showss in show:
    shows.append({
      'venue_id': showss.venue.id,
      'venue_name': showss.venue.name,
      'artist_name': showss.artist.name,
      'artist_id': showss.artist_id,
      'artist_image_link': showss.artist.image_link,
      'start_time': str(showss.show_time.strftime('%Y -%m-%d %H:%M:S'))
    }) 


  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  # renders form. do not touch.
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    form = ShowForm(request.form)
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    show_time = Shows(artist_id=artist_id, venue_id=venue_id, show_time =start_time)
    
    db.session.add(show_time)
    db.session.commit()
    flash('Show was successfully listed!')
    
  except:
      db.session.rollback()
      flash('Show could not be listed')
      
  finally:
      db.session.close()
      return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
