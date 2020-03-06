# -*- coding: utf-8 -*-
import re
import scrapy
import logging
from ohakaguide.items import OhakaguideItem

# HTTPヘッダー X-Robots-Tagをチェック


def validate_robot_headers(headers, value):
  robots = headers.get('X-Robots-Tag')
  return robots != None and re.search(value, robots.decode('utf-8'))

# meta robotを確認する


def validate_robot_meta(selector, value):
  included = False
  metadata = selector.css('html > head > meta')
  for meta in metadata:
    name = meta.css('::attr(name)').extract_first()
    if name == 'robots':
      content = meta.css('::attr(content)').extract_first()
      if content != None and re.search(value, content):
        included = True

  return included

# aタグのリンクタイプに'nofollow'が含まれている場合、
# そのリンクは辿ることは不可とされている


def can_follow_link(a):
  linktypes = a.css('::attr(rel)').extract_first()
  return (linktypes == None) or ('nofollow' not in linktypes.split(' '))


class OhakaguideSpiderSpider(scrapy.Spider):
  name = 'ohakaguide-spider'
  allowed_domains = ['ohakaguide.com']
  start_urls = ['http://ohakaguide.com/temple/']
  serial = 0

  def parse(self, response):

    if validate_robot_meta(response, 'none'):
      logging.error('robot meta: noindex + nofollow')
      return

    if validate_robot_meta(response, 'noindex'):
      logging.error('robot meta: noindex')
      return

    if validate_robot_meta(response, 'nofollow'):
      logging.error('robot meta: noindex')
      return

    if validate_robot_meta(response, 'noarchive'):
      logging.error('robot meta: noindex')
      return

    for a in response.css('#temple_list_top > dl > dd > a'):
      url = a.css('::attr(href)').extract_first()
      if can_follow_link(a):
        yield scrapy.Request(url, callback=self.parse_item)
      else:
        logging.error('Can not Follow Link: <%s>' % url)

  def parse_item(self, response):
    for tr in response.css('#area02 > table > tr'):
      data = {}
      keys = ['name', 'sect', 'addr']
      for i, td in enumerate(tr.css('tr > td')):
        data[keys[i]] = td.css('::text').extract_first()

      if len(data) > 0:
        self.serial = self.serial + 1
        item = OhakaguideItem()
        item['serial'] = self.serial
        item['data'] = data
        yield item
