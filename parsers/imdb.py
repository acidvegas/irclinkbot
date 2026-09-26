#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/imdb.py

import re

from fetch      import get_json
from formatting import BLACK, GREY, YELLOW, bold, clean, color, line, number, site_tag


TAG     = site_tag('IMDb', BLACK, YELLOW)
API     = 'https://caching.graphql.imdb.com/'
HEADERS = {'Origin': 'https://www.imdb.com', 'x-imdb-client-name': 'imdb-web-next'}
QUERY   = 'query($id:ID!){title(id:$id){titleText{text} releaseYear{year endYear} ratingsSummary{aggregateRating voteCount} runtime{seconds} genres{genres{text}} titleType{text} certificate{rating} plot{plotText{plainText}}}}'


async def title(session, match: re.Match) -> str | None:
	'''
	Parse an IMDb title link using IMDb's public GraphQL API (the one imdb.com itself uses)

	:param session: HTTP session
	:param match: Regex match with the title id as group 1
	'''

	data = (await get_json(session, API, headers=HEADERS, json={'query': QUERY, 'variables': {'id': match.group(1)}}))['data']['title']

	if not data:
		return

	year    = data.get('releaseYear') or {}
	years   = f'{year["year"]}–{year["endYear"] or ""}' if year.get('endYear') or (data.get('titleType') or {}).get('text', '').startswith('TV Series') else str(year.get('year', ''))
	rating  = data.get('ratingsSummary') or {}
	runtime = (data.get('runtime') or {}).get('seconds')
	plot    = ((data.get('plot') or {}).get('plotText') or {}).get('plainText')

	return line(TAG,
		bold(clean(data['titleText']['text'], 150)) + (color(f' ({years})', GREY) if year.get('year') else ''),
		(data.get('titleType') or {}).get('text'),
		f'{rating["aggregateRating"]}/10 ' + color(f'({number(rating["voteCount"])} votes)', GREY) if rating.get('aggregateRating') else None,
		(f'{runtime // 3600}h {runtime % 3600 // 60}m' if runtime >= 3600 else f'{runtime // 60}m') if runtime else None,
		', '.join(genre['text'] for genre in (data.get('genres') or {}).get('genres', [])[:3]) or None,
		(data.get('certificate') or {}).get('rating'),
		clean(plot, 150) if plot else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?imdb\.com/(?:[a-z]{2}/)?title/(tt\d+)'), title),
)
