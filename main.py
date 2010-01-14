#!/usr/bin/env python
#
# annotatr
# Copyright 2009 - Bosco Ho and Mark Reid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.appengine.api import users
# from google.appengine.api import urlfetch    # Instead of urllib ?

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util, template

from BeautifulSoup import BeautifulSoup
from mako.template import Template

from models import Article

import citeulike

from datetime import datetime
import os
import urllib
import re
import cgi

class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(open('views/index.html').read())

class SearchHandler(webapp.RequestHandler):
  def get(self):
    search_terms = self.request.get('q')
    parms = {'q': search_terms}
    i_page = unicode(self.request.get('page'))
    if i_page:
      parms['page'] = i_page 
    query_string = urllib.urlencode(parms)
    url = 'http://www.citeulike.org/search/all?'
    socket = urllib.urlopen(url+query_string)
    txt = socket.read()
    socket.close()
    entries, pages = citeulike.search_metadata(txt, i_page)
    attrs = {
        'entries': entries, 
        'query': 'citeulike.org/search/all?'+query_string.lower(),
        'search_pages': pages}
    template = Template(open('views/search.html').read())
    s = template.render_unicode(attributes=attrs)
    self.response.out.write(s)

class ArticleHandler(webapp.RequestHandler):
  def get(self):
    path = self.request.path.replace('citeulike/', '')
    url = 'http://www.citeulike.org' + path
    socket = urllib.urlopen(url)

    # Build template
    template = Template(open('views/page.html').read())
    attrs = citeulike.page_metadata(socket.read(), url)
    attrs['views'] = Article.all().filter("id =", self.request.path).count()
    s = template.render_unicode(attributes=attrs)

    # Render the page
    self.response.out.write(template.render_unicode(attributes=attrs))

    # Record that this article has been viewed
    article = Article(id=self.request.path, last_viewed=datetime.now())
    article.put()
     
def main():
  application = webapp.WSGIApplication(
      [('/', MainHandler), 
       ('/search/all', SearchHandler),
       ('/.*', ArticleHandler)],
      debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
