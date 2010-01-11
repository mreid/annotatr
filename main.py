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
from google.appengine.ext.webapp import util

from BeautifulSoup import BeautifulSoup
from mako.template import Template

import urllib
import re
import cgi

index_template = """
<html>
<head>
<title>annotatr</title>
<link rel="stylesheet" type="text/css" media="screen" href="/styles/style.css"/> 
</head>
<body>
<div id="container">
  <div id="header">annotatr</div>
  <div id="tagline">citeulike+disqus mashup</div>
                
  <div class="abstract" style="text-align:center">
    Find abstracts and comment on them.
  </div>

  <div id="search_bar">
    <form method="get" action="/search/all">
    <input type="text" name="q" style="width:470px"/>
    <input type="submit" value="Search" />
  </div>

  <div class="abstract" style="color:#AAA; text-align:center">
    search examples
    <br>
    <br>
    <a href="/search/all?q=beta+%26%26+sheet*+%21alpha+%21helix">beta && sheet* !alpha !helix</a>
    <br>
    <a href="/search/all?q=author%3A%22franklin+r+e%22">author:"franklin r e"</a>
    <br>
    <a href="/search/all?q=year%3A2007+journal%3Anature">year:2007 journal:nature</a>
    <br>
    <a href="/search/all?q=year%3A%5B1995+TO+1997%5D">year:[1995 TO 1997]</a>
  </div>


</form>
</div>
</body>
</html>
"""

class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(index_template)


class StyleHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(open('style.css').read())


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
       'link': link,
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


search_template = u"""
<html>
<head>
<title>annotatr</title>
<link rel="stylesheet" type="text/css" media="screen" href="/styles/style.css"/> 
</head>
</head>
<body>
<div id="container">
  <div id="small_header"><a href="/">annotatr</a></div>
  <div id="small_tagline">citeulike+disqus mashup</div>

  <div id="search_bar">
    <form method="get" action="/search/all">
    <input type="text" name="q" style="width:470px"/>
    <input type="submit" value="Search" />
  </div>

  <div id="search_term">
    ${attributes['query']}
  </div>
  
  % for entry in attributes['entries']:
  <div class="search_entry">
    <div class="search_title">
      <a href="/citeulike${entry['link']}">${entry['title']}</a>
    </div>
    <div class="search_authors">
      ${entry['authors']}
    </div>
    <div class="search_reference">
      <i>${entry['reference']}</i>
    </div>
  </div>
  % endfor
  
  <div class="page_links">
    % for search_page in attributes['search_pages']:
    <div class="button">
      ${search_page}
    </div>  
    % endfor
    <br clear=all>
  </div>
  
</div>
</body>
</html>
"""


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
    template = Template(search_template)
    s = template.render_unicode(attributes=attrs)
    self.response.out.write(s)


def metadata_from_citeulike_page(txt, url):
  attrs = {
      'tittle': '',
      'author': '',
      'reference': '',
      'links': [('citeulike', url)],
      'abstract': '',
  }
  soup = BeautifulSoup(txt)
  title = soup.find('h1')
  attrs['title'] = title.contents[0]
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


page_template = u"""
<html>
<head>
<title>annotatr</title>
<link rel="stylesheet" type="text/css" media="screen" href="/styles/style.css"/> 
</head>
<body>
<div id="container">
  <div id="small_header"><a href="/">annotatr</a></div>
  <div id="small_tagline">citeulike+disqus mashup</div>

  <div id="search_bar">
    <form method="get" action="/search/all">
    <input type="text" name="q" style="width:470px"/>
    <input type="submit" value="Search" />
  </div>

  <div class="title">
    ${attributes['title']}
  </div>

  <div class="authors">
    ${attributes['author']}
  </div>

  <div class="reference">
    <i>${attributes['reference']}</i>
  </div>

  <div class="links">
    % for label, link in attributes['links']:
    <div class="button">
      <a href="${link}">${label}</a>
    </div>
    % endfor
    <br clear="all">
  </div>

  <div class="abstract">
    ${attributes['abstract']}
  </div>

  <script type="text/javascript">
//<![CDATA[
(function() {
	var links = document.getElementsByTagName('a');
	var query = '?';
	for(var i = 0; i < links.length; i++) {
	if(links[i].href.indexOf('#disqus_thread') >= 0) {
		query += 'url' + i + '=' + encodeURIComponent(links[i].href) + '&';
	}
	}
	document.write('<script charset="utf-8" type="text/javascript" src="http://disqus.com/forums/annotatr/get_num_replies.js' + query + '"></' + 'script>');
})();
//]]>
  </script>

  <div id="disqus_thread"></div><script type="text/javascript" src="http://disqus.com/forums/annotatr/embed.js"></script><noscript><a href="http://disqus.com/forums/annotatr/?url=ref">View the discussion thread.</a></noscript>

  <div style="width:100%; height:8em">
    &nbsp;
  </div>

</body>
</html>
"""


class ArticleHandler(webapp.RequestHandler):
  def get(self):
    path = self.request.path.replace('citeulike/', '')
    url = 'http://www.citeulike.org' + path
    socket = urllib.urlopen(url)
    opened_url = socket.geturl()
    if url != opened_url:
      path = opened_url.replace('http://www.citeulike.org/', '')
      self.redirect('/citeulike/' + path)
    else:
      template = Template(page_template)
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
