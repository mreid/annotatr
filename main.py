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
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util, template

from BeautifulSoup import BeautifulSoup
from mako.template import Template

import os
import urllib
import re
import cgi

class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(open('views/index.html').read())

def contents_unicode(contents, separator=""):
  s = u""
  for x in contents:
    if s:
      s += separator
    try:
      new_s = unicode(x)
    except:
      new_s = ""
    s += new_s
  return s

def canonical_citeulike_link(link):
   pattern = re.compile('/article/\d+$')
   return pattern.search(link).group()

def metadata_from_citeulike_search(txt, i_page):
  soup = BeautifulSoup(txt)
  entries = []
  for e in soup.findAll('td', {'class':'list_item '}):
    link = e.find('a', {'class':'title'})
    title = link.string
    link = link['href']
    pieces = e.findAll('div', {'class':'vague'})
    reference, authors = "", ""
    if pieces:
      reference = contents_unicode(pieces[0].contents)
      if len(pieces) > 1:
        author_links = pieces[1].contents[1::2]
        authors = contents_unicode([a.string for a in author_links], ", ")
    entry = {
       'title': title,
       'authors': authors,
       'link': canonical_citeulike_link(link),
       'reference': reference }
    entries.append(entry)
  pages = []
  for e in soup.findAll('a', {'rel':'nofollow'}):
    link = e['href']
    if re.search(r'page=\d+$', link):
      pages.append(link)
  search_pages = []
  if pages:
    pages = list(set(pages))
    pairs = {}
    for page in pages:
      i = int(re.search(r'\d+$', page).group())
      pairs[i] = page
    vals = pairs.keys()
    for i in range(min(vals), max(vals)+1):
      if i not in vals:
        search_pages.append(">%d<" % i)
      else:
        search_pages.append('<a href="%s">%d</a>' % (pairs[i], i))
  return entries, search_pages


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
    entries, pages = \
       metadata_from_citeulike_search(txt, i_page)
    attrs = {
        'entries': entries, 
        'query': 'citeulike.org/search/all?'+query_string.lower(),
        'search_pages': pages}
    template = Template(open('views/search.html').read())
    s = template.render_unicode(attributes=attrs)
    self.response.out.write(s)


def metadata_from_citeulike_page(txt, url):
  attrs = {
      'title': '',
      'author': '',
      'reference': '',
      'links': [('citeulike', url)],
      'abstract': '',
  }
  soup = BeautifulSoup(txt)
  title = soup.find('h1')
  attrs['title'] = title.contents[0].rstrip()
  piece = title.nextSibling.nextSibling.nextSibling.nextSibling
  for author in piece.contents[1::2]:
    if attrs['author']:
      attrs['author'] += ", "
    attrs['author'] += unicode(author.contents[0])
  reference = piece.nextSibling.nextSibling
  if len(reference.contents) > 1:
    for x in reference.contents[1].contents:
      attrs['reference'] += unicode(x)
  abstract = soup.find('div', {'id':'abstract-body'})
  if abstract:
    for x in abstract.contents[1].contents:
      attrs['abstract']  += unicode(x)
  link_section = soup.find('span', {'id':'linkouts'})
  if link_section:
    for link in link_section.findAll('a'):
      if link['href'] != "#":
        attrs['links'].append((link.string, link['href']))
  return attrs


class ArticleHandler(webapp.RequestHandler):
  def get(self):
    path = self.request.path.replace('citeulike/', '')
    url = 'http://www.citeulike.org' + path
    socket = urllib.urlopen(url)
    # opened_url = socket.geturl()
    # if url != opened_url:
    #   path = opened_url.replace('http://www.citeulike.org/', '')
    #   self.redirect('/citeulike/' + path)
    # else:
    template = Template(open('views/page.html').read())
    attrs = metadata_from_citeulike_page(socket.read(), url)
    s = template.render_unicode(attributes=attrs)
    self.response.out.write(template.render_unicode(attributes=attrs))
 
def main():
  application = webapp.WSGIApplication(
      [('/', MainHandler), 
       ('/search/all', SearchHandler),
       ('/.*', ArticleHandler)],
      debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
