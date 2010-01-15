import datetime
from google.appengine.ext import db

# A simple Article class that models when an article has been viewed.
class Article(db.Model):
   id          = db.StringProperty(required=True)
   last_viewed = db.DateTimeProperty()

# Keeps track of searches
class Search(db.Model):
   query       = db.StringProperty(required=True)
   encoded     = db.StringProperty(required=True)
   searched_at = db.DateTimeProperty()