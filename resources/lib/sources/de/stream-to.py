# -*- coding: utf-8 -*-

"""
    Lastship Add-on (C) 2017
    Credits to Exodus and Covenant; our thanks go to their creators

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import re
import urllib
import urlparse

from resources.lib.modules import cleantitle, cfscrape
from resources.lib.modules import client
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules.recaptcha import recaptcha_app


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['stream.to']
        self.base_link = 'https://stream.to'
        self.search_link = '/ajax/suggest_search'
        self.get_player = '/ajax/load_player/%s'
        self.get_link = '/ajax/load_video/%s'
        self.recapInfo = ""
        self.scraper = cfscrape.create_scraper()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases))
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            url = url.replace('/en/', '/de/')

            video_id = re.search('(?<=\/)(\d*?)(?=-)', url).group()
            if not video_id:
                return sources

            # load player
            query = self.get_player % (video_id)
            query = urlparse.urljoin(self.base_link, query)
            r = client.request(query)

            r = dom_parser.parse_dom(r, 'div', attrs={'class': 'le-server'})

            # for each hoster
            for i in r:
                hoster = dom_parser.parse_dom(i, 'div', attrs={'class': 'les-title'})
                hoster = dom_parser.parse_dom(hoster, 'strong')
                hoster = hoster[0][1]

                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                links = dom_parser.parse_dom(i, 'a', attrs={'class': 'ep-item'})

                # for each link
                for i in links:
                    if '1080p' in i[0]['title']:
                        quality = '1080p'
                    elif 'HD' in i[0]['title']:
                        quality = 'HD'
                    else:
                        quality = 'SD'

                    url = i[0]['id']
                    if not url: continue

                    sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': False, 'debridonly': False, 'checkquality': True, 'captcha': True})

            return sources
        except:
            return sources

    def resolve(self, url):
        try:

            query = self.get_link % (url)
            query = urlparse.urljoin(self.base_link, query)
            r = client.request(query)

            url = dom_parser.parse_dom(r, 'iframe', req='src')
            url = url[0][0]['src']

            recap = recaptcha_app.recaptchaApp()
            key = recap.getSolutionWithDialog(urlparse.urljoin(self.base_link, url), "6LcY-20UAAAAAFWIgEPEs8lnd7Wxfq_NAtYt29dG", self.recapInfo)
            print "Recaptcha2 Key: " + key

            response = None

            if key != "" and "skipped" not in key.lower():
                response = self.scraper.get(urlparse.urljoin(self.base_link, url) + "?typ=v2&token=" + key)
            elif not response or "skipped" in key.lower():
                return

            if response is not None:
                url = response.url

            return url
        except:
            return url

    def __search(self, titles):
        try:
            query = urlparse.urljoin(self.base_link, self.search_link)
            post = urllib.urlencode({'keyword': titles[0]})

            t = [cleantitle.get(i) for i in set(titles) if i]

            r = client.request(query, post=post)
            r = json.loads(r)
            r = r['content']

            r = dom_parser.parse_dom(r, 'li')

            for i in r:
                title = dom_parser.parse_dom(i[1], 'a', attrs={'class': 'ss-title'})
                if cleantitle.get(title[0][1]) in t:
                    return source_utils.strip_domain(title[0][0]['href'])
        except:
            return

    def setRecapInfo(self, info):
        self.recapInfo = info
