#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/telegram.py

import re

from fetch           import get_text
from formatting      import CYAN, LIGHTBLUE, WHITE, ago, bold, clean, color, line, site_tag, stat, timestamp
from parsers.generic import meta_tags


TAG = site_tag('Telegram', WHITE, LIGHTBLUE)


async def channel(session, match: re.Match) -> str | None:
	'''
	Parse a Telegram channel, group, or user link from its public preview page

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	page  = await get_text(session, f'https://t.me/{match.group(1)}')
	title = re.search(r'class="tgme_page_title"[^>]*>(.*?)</div>', page, re.S)
	extra = re.search(r'class="tgme_page_extra">([^<]+)<', page)

	if not title:
		return

	return line(TAG,
		bold(clean(title.group(1), 100)),
		clean(meta_tags(page).get('og:description', ''), 150),
		clean(extra.group(1), 50) if extra else None
	)


async def post(session, match: re.Match) -> str | None:
	'''
	Parse a public Telegram channel post link from its embed page

	:param session: HTTP session
	:param match: Regex match with the channel as group 1 & post id as group 2
	'''

	page  = await get_text(session, f'https://t.me/{match.group(1)}/{match.group(2)}?embed=1&mode=tme')
	owner = re.search(r'class="tgme_widget_message_owner_name"[^>]*>(.*?)</a>', page, re.S)
	text  = re.search(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', page, re.S)
	views = re.search(r'class="tgme_widget_message_views">([^<]+)<', page)
	stamp = re.search(r'datetime="([^"]+)"', page)

	if not owner:
		return

	return line(TAG,
		color(clean(owner.group(1), 50), CYAN) + ': ' + (clean(text.group(1).replace('<br/>', ' '), 250) if text else '[media]'),
		stat(views.group(1), 'views') if views else None,
		ago(timestamp(stamp.group(1))) if stamp else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?(?:t|telegram)\.me/(?:s/)?(\w{4,})/(\d+)'),         post),
	(re.compile(r'https?://(?:www\.)?(?:t|telegram)\.me/(?!joinchat|addstickers|share|proxy)(\w{4,})/?(?:[?#].*)?$'), channel),
)
