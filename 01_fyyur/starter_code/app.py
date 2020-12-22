#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import Integer, ForeignKey, String, Column, func, update
from sqlalchemy.orm import relationship
import datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class show_info(db.Model):
  __tablename__ = 'show_info'

  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
  start_time = db.Column(db.String(120), primary_key=True)
  
  artist = db.relationship('Artist', back_populates='venues')
  venue = db.relationship('Venue', back_populates='artists')


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))

    artists = db.relationship('show_info', back_populates='venue')

    # database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))

    venues = db.relationship('show_info', back_populates='artist')

    # database migration using Flask-Migrate

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  shows=db.session.query(Venue,show_info).outerjoin(show_info).order_by(Venue.id).all()  
  venuess=db.session.query(Venue).filter_by().all()
  
  data = [dict(
    city=venue.city, 
    state=venue.state,
    venues=[dict(id=v.id, name=v.name) for v in venuess if venue.city==v.city]
    ) for venue in venuess]
  
  data=[i for n, i in enumerate(data) if i not in data[n + 1:]] 
  num = []
  for i in range(len(venuess)):
    upcoming_shows = 0
    for show in shows:
      if show[0].id==i+1 and show[1] is not None:
        upcoming_shows += 1
      elif show[0].id==i+1 and show[1] is None:
        upcoming_shows +=0
    num.append(upcoming_shows) 

  for i in range(len(num)):
    for dat in data:
      for venue in dat['venues']:
        if venue['id']==i+1:
          venue['num_upcoming_shows']=num[i]

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['GET','POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  if request.method=="POST":
    search = request.form.get("search_term")
    
    data = db.session.query(Venue,show_info).join(show_info, show_info.venue_id==Venue.id).filter(Venue.name.ilike(f'%{search}%')).all()
    counter=db.session.query(Venue).filter(Venue.name.ilike(f'%{search}%')).all()
  
    response=dict(count=len(counter), data=[dict(id=v[0].id, name=v[0].name, num_upcoming_shows=len([v[1] for v in data])) for v in data])

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id  
  v=db.session.query(show_info,Artist,Venue).join(Artist, Artist.id==show_info.artist_id).join(Venue, Venue.id==show_info.venue_id).filter_by(id=venue_id).all()
  
  if len(v)==0:    
    v=db.session.query(Venue).filter_by(id=venue_id).all()
    for i in range(len(v)):
      data=dict(id=v[i].id, name=v[i].name, genres=v[i].genres, address=v[i].address, city=v[i].city, state=v[i].state,
      phone=v[i].phone, website=v[i].website, facebook_link=v[i].facebook_link, seeking_talent=v[i].seeking_talent,
      seeking_description=v[i].seeking_description, image_link=v[i].image_link, 
      past_shows=[],
      upcoming_shows=[])
  else:
    for i in range(len(v)):
      data=dict(id=v[i][2].id, name=v[i][2].name, genres=v[i][2].genres, address=v[i][2].address, city=v[i][2].city, state=v[i][2].state,
      phone=v[i][2].phone, website=v[i][2].website, facebook_link=v[i][2].facebook_link, seeking_talent=v[i][2].seeking_talent,
      seeking_description=v[i][2].seeking_description, image_link=v[i][2].image_link, 
      past_shows=[dict(artist_id=v[i][0].artist_id,artist_name=v[i][1].name, artist_image_link=v[i][1].image_link, start_time=v[i][0].start_time) 
      for i in range(len(v)) if v[i][0].start_time<=datetime.datetime.now().isoformat()],
      upcoming_shows=[dict(artist_id=v[i][0].artist_id,artist_name=v[i][1].name, artist_image_link=v[i][1].image_link, start_time=v[i][0].start_time) 
      for i in range(len(v)) if v[i][0].start_time>datetime.datetime.now().isoformat()])

  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  body = {}
  try:
    newV = Venue()
    newV.name = request.form.get("name")
    newV.city = request.form.get("city")
    newV.state = request.form.get("state")
    newV.address = request.form.get("address")
    newV.phone = request.form.get("phone")
    #newV.image_link = db.Column(db.String(500))
    newV.facebook_link = request.form.get("facebook_link")
    #newV.seeking_talent = db.Column(db.Boolean)
    #newV.seeking_description = db.Column(db.String(500))
    #newV.website = db.Column(db.String(120))
    newV.genres = request.form.getlist("genres")
    
    body['name'] = newV.name
    body['city'] = newV.city
    body['state'] = newV.state
    body['address'] = newV.address
    body['phone'] = newV.phone
    #body['image_link'] = newV.image_link
    body['facebook_link'] = newV.facebook_link
    #body[''] = newV.seeking_talent 
    #body[''] = newV.seeking_description 
    #body[''] = newV.website 
    body['genres'] = newV.genres

    db.session.add(newV)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort (400)
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')   
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index')) and jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  info = db.session.query(Artist).all()
  data=[dict(id=a.id, name=a.name)for a in info]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  if request.method=="POST":
    search = request.form.get('search_term')
    
    data = db.session.query(Artist,show_info).join(show_info, show_info.artist_id==Artist.id).filter(Artist.name.ilike(f'%{search}%')).all()
    counter=db.session.query(Artist).filter(Artist.name.ilike(f'%{search}%')).all()
  
    response=dict(count=len(counter), data=[dict(id=v[0].id, name=v[0].name, num_upcoming_shows=len([v[1] for v in data])) for v in data])

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  v=db.session.query(show_info,Venue,Artist).join(Venue, Venue.id==show_info.venue_id).join(Artist, Artist.id==show_info.artist_id).filter_by(id=artist_id).all()
  
  if len(v)==0:    
    v=db.session.query(Artist).filter_by(id=artist_id).all()
    for i in range(len(v)):
      data=dict(id=v[i].id, name=v[i].name, genres=v[i].genres, city=v[i].city, state=v[i].state,
      phone=v[i].phone, website=v[i].website, facebook_link=v[i].facebook_link, seeking_venue=v[i].seeking_venue,
      seeking_description=v[i].seeking_description, image_link=v[i].image_link, 
      past_shows=[],
      upcoming_shows=[])
  else:
    for i in range(len(v)):
      data=dict(id=v[i][2].id, name=v[i][2].name, genres=v[i][2].genres, city=v[i][2].city, state=v[i][2].state,
      phone=v[i][2].phone, website=v[i][2].website, facebook_link=v[i][2].facebook_link, seeking_venue=v[i][2].seeking_venue,
      seeking_description=v[i][2].seeking_description, image_link=v[i][2].image_link, 
      past_shows=[dict(venue_id=v[i][0].venue_id, venue_name=v[i][1].name, venue_image_link=v[i][1].image_link, start_time=v[i][0].start_time) 
      for i in range(len(v)) if v[i][0].start_time<=datetime.datetime.now().isoformat()],
      upcoming_shows=[dict(venue_id=v[i][0].venue_id,venue_name=v[i][1].name, venue_image_link=v[i][1].image_link, start_time=v[i][0].start_time) 
      for i in range(len(v)) if v[i][0].start_time>datetime.datetime.now().isoformat()])

  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  a = db.session.query(Artist).filter_by(id=artist_id).all()
  artist = dict(id=a[0].id, name=a[0].name, genres=a[0].genres, city=a[0].city, state=a[0].state, phone=a[0].phone, 
  webiste=a[0].website, facebook_link=a[0].facebook_link, seeking_venue=a[0].seeking_venue, seeking_description=a[0].seeking_description,
  image_link=a[0].image_link)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # Take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)
  artist.name = request.form.get("name"),
  artist.city = request.form.get("city"),
  artist.state = request.form.get("state"),
  artist.phone = request.form.get("phone"),
    #newV.image_link = db.Column(db.String(500)),
  artist.facebook_link = request.form.get("facebook_link"),
    #newV.seeking_talent = db.Column(db.Boolean),
    #newV.seeking_description = db.Column(db.String(500)),
    #newV.website = db.Column(db.String(120)),
  artist.genres = request.form.getlist("genres")
  db.session.add(artist)
  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  a = db.session.query(Venue).filter_by(id=venue_id).all()
  venue = dict(id=a[0].id, name=a[0].name, genres=a[0].genres,address=a[0].address, city=a[0].city, state=a[0].state, phone=a[0].phone, 
  webiste=a[0].website, facebook_link=a[0].facebook_link, seeking_talent=a[0].seeking_talent, seeking_description=a[0].seeking_description,
  image_link=a[0].image_link)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  #venue= (update(Venue).where(Venue.id==venue_id).values(
  venue.name = request.form.get("name"),
  venue.city = request.form.get("city"),
  venue.state = request.form.get("state"),
  venue.address = request.form.get("address"),
  venue.phone = request.form.get("phone"),
    #newV.image_link = db.Column(db.String(500)),
  venue.facebook_link = request.form.get("facebook_link"),
    #newV.seeking_talent = db.Column(db.Boolean),
    #newV.seeking_description = db.Column(db.String(500)),
    #newV.website = db.Column(db.String(120)),
  venue.genres = request.form.getlist("genres")
  db.session.add(venue)
  db.session.commit()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  try:
    newV = Artist()
    newV.name = request.form.get("name")
    newV.city = request.form.get("city")
    newV.state = request.form.get("state")
    newV.phone = request.form.get("phone")
    #newV.image_link = db.Column(db.String(500))
    newV.facebook_link = request.form.get("facebook_link")
    #newV.seeking_talent = db.Column(db.Boolean)
    #newV.seeking_description = db.Column(db.String(500))
    #newV.website = db.Column(db.String(120))
    newV.genres = request.form.getlist("genres")
    
    db.session.add(newV)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort (400)
    # On unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')   

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  
  v=db.session.query(show_info,Artist,Venue).join(Artist, Artist.id==show_info.artist_id).join(Venue, Venue.id==show_info.venue_id).all()
  
  data=[dict(venue_id=v[2].id, venue_name=v[2].name, artist_id=v[0].artist_id,artist_name=v[1].name, artist_image_link=v[1].image_link, 
  start_time=v[0].start_time) for v in v]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    newV = show_info()
    newV.venue_id = request.form.get("venue_id")
    newV.artist_id = request.form.get("artist_id")
    newV.start_time = request.form.get("start_time")
    
    db.session.add(newV)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort (400)
    # On unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
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
