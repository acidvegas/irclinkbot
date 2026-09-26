#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/letterboxd.py

import re

from fetch           import get_text
from formatting      import BLACK, GREY, LIGHTGREEN, bold, clean, color, line, number, site_tag
from parsers.generic import json_ld


TAG = site_tag('Letterboxd', LIGHTGREEN, BLACK)


async def film(session, match: re.Match) -> str | None:
	'''
	Parse a Letterboxd film link from the page's JSON-LD data

	:param session: HTTP session
	:param match: Regex match with the film slug as group 1
	'''

	if not (data := json_ld(await get_text(session, f'https://letterboxd.com/film/{match.group(1)}/'), 'Movie')):
		return

	rating = data.get('aggregateRating') or {}
	year   = (data.get('dateCreated') or '')[:4]

	return line(TAG,
		bold(clean(data['name'], 150)) + (color(f' ({year})', GREY) if year else ''),
		f'{rating["ratingValue"]:.2f}/5 ' + color(f'({number(rating.get("ratingCount", 0))} ratings)', GREY) if rating.get('ratingValue') else None,
		'dir. ' + ', '.join(person['name'] for person in data.get('director', [])[:2]) if data.get('director') else None,
		', '.join(data.get('genre', [])[:3]) or None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?letterboxd\.com/(?:\w+/)?film/([\w-]+)'), film),
)
