# CiteULke specific code for search and page scraping

from BeautifulSoup import BeautifulSoup

import re

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

def make_link(link):
   pattern = re.compile('/article/\d+$')
   return pattern.search(link).group()

def page_metadata(txt, url):
  attrs = {
      'title': '',
      'author': '',
      'reference': '',
      'links': [('citeulike', url)],
      'abstract': '',
  }
  soup = BeautifulSoup(txt)
  title = soup.find('h1')
  attrs['title'] = title.contents[0].string.rstrip()
  author_links = soup.findAll('a', {"class":"author"})
  for author_link in author_links:
    if attrs['author']:
      attrs['author'] += u", "
    attrs['author'] += unicode(author_link.string)
  reference = soup.find('div', {'id': 'citation'})
  if reference and len(reference.contents) > 1:
    for x in reference.contents:
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

def search_metadata(txt, i_page):
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
       'link': make_link(link),
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

