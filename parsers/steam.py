#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/steam.py

import asyncio
import re

from fetch      import get_json
from formatting import BLUE, GREEN, GREY, LIGHTCYAN, bold, clean, color, line, number, site_tag


TAG = site_tag('Steam', LIGHTCYAN, BLUE)


async def app(session, match: re.Match) -> str | None:
	'''
	Parse a Steam store link using the public store API

	:param session: HTTP session
	:param match: Regex match with the app id as group 1
	'''

	app_id = match.group(1)
	details, reviews = await asyncio.gather(
		get_json(session, f'https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=en'),
		get_json(session, f'https://store.steampowered.com/appreviews/{app_id}?json=1&language=all&purchase_type=all&num_per_page=0')
	)
	result = next(iter(details.values())) # Steam sometimes keys the result by a different app id

	if not result.get('success'):
		return

	data    = result['data']
	reviews = reviews.get('query_summary', {})

	if data.get('is_free'):
		price = color('Free', GREEN)
	elif price := data.get('price_overview'):
		price = price['final_formatted'] + (color(f' (-{price["discount_percent"]}%)', GREEN) if price.get('discount_percent') else '')

	return line(TAG,
		bold(clean(data['name'], 150)),
		price or None,
		f'{reviews["review_score_desc"]} ' + color(f'({number_reviews(reviews)})', GREY) if reviews.get('total_reviews') else None,
		', '.join(genre['description'] for genre in data.get('genres', [])[:3]) or None,
		', '.join(data.get('developers', [])[:2]) or None,
		color(data['release_date']['date'], GREY) if data.get('release_date', {}).get('date') else None,
		nsfw=int(data.get('required_age') or 0) >= 18
	)


def number_reviews(reviews: dict) -> str:
	'''
	Format the review summary as the percentage positive & total reviews

	:param reviews: Steam review query_summary
	'''

	return f'{reviews["total_positive"] * 100 // reviews["total_reviews"]}% of {number(reviews["total_reviews"])} reviews'


ROUTES = (
	(re.compile(r'https?://store\.steampowered\.com/app/(\d+)'), app),
	(re.compile(r'https?://steamcommunity\.com/app/(\d+)'),      app),
)
