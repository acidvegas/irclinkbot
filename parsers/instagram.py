#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/instagram.py

import html
import re

from fetch           import EMBED_UA, get_text
from formatting      import CYAN, GREY, PINK, WHITE, clean, color, line, site_tag, stat
from parsers.generic import meta_tags


TAG     = site_tag('Instagram', WHITE, PINK)
HEADERS = {'User-Agent': EMBED_UA} # Instagram only serves OpenGraph tags to link preview crawlers


async def post(session, match: re.Match) -> str | None:
	'''
	Parse an Instagram post or reel link from its OpenGraph tags

	:param session: HTTP session
	:param match: Regex match of the post URL
	'''

	tags = meta_tags(await get_text(session, match.group(0), headers=HEADERS))

	if not (description := html.unescape(tags.get('og:description', '')).strip()):
		return

	if not (info := re.match(r'([\d.,KMB]+) likes?, ([\d.,KMB]+) comments? - ([\w.]+) on ([^:]+): "?(.*?)"?\.?$', description, re.S)):
		return line(TAG, clean(tags.get('og:title', ''), 150), clean(description, 200))

	likes, comments, username, date, caption = info.groups()
	name                                     = clean(html.unescape(tags.get('og:title', '')).split(' on Instagram', 1)[0], 50)

	return line(TAG,
		color(name, CYAN) + color(f' (@{username})', GREY) + ': ' + clean(caption, 200),
		stat(likes, 'likes'),
		stat(comments, 'comments'),
		color(date, GREY)
	)


async def profile(session, match: re.Match) -> str | None:
	'''
	Parse an Instagram profile link from its OpenGraph tags

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	if match.group(1).lower() in ('accounts', 'explore', 'direct', 'stories', 'about', 'developer', 'legal'):
		return

	tags = meta_tags(await get_text(session, match.group(0), headers=HEADERS))

	if not (info := re.match(r'([\d.,KMB]+) Followers, ([\d.,KMB]+) Following, ([\d.,KMB]+) Posts', html.unescape(tags.get('og:description', '')))):
		return

	return line(TAG,
		color(clean(html.unescape(tags.get('og:title', '')).split(' • ', 1)[0], 80), CYAN),
		stat(info.group(1), 'followers'),
		stat(info.group(3), 'posts')
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?instagram\.com/(?:[\w.]+/)?(?:p|reels?|tv)/[\w-]+'), post),
	(re.compile(r'https?://(?:www\.)?instagram\.com/([\w.]+)/?(?:[?#].*)?$'),           profile),
)
