#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/arxiv.py

import re
import xml.etree.ElementTree as ET

from fetch      import get_text
from formatting import GREY, RED, WHITE, bold, clean, color, line, site_tag


TAG  = site_tag('arXiv', WHITE, RED)
ATOM = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}


async def paper(session, match: re.Match) -> str | None:
	'''
	Parse an arXiv paper link using the public export API

	:param session: HTTP session
	:param match: Regex match with the paper id as group 1
	'''

	entry = ET.fromstring(await get_text(session, f'https://export.arxiv.org/api/query?id_list={match.group(1)}')).find('atom:entry', ATOM)

	if entry is None or entry.find('atom:title', ATOM) is None:
		return

	authors  = [author.findtext('atom:name', '', ATOM) for author in entry.findall('atom:author', ATOM)]
	category = entry.find('arxiv:primary_category', ATOM)

	return line(TAG,
		bold(clean(entry.findtext('atom:title', '', ATOM), 200)),
		', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else ''),
		category.get('term') if category is not None else None,
		color(entry.findtext('atom:published', '', ATOM)[:10], GREY)
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|export\.)?arxiv\.org/(?:abs|pdf|html)/([\w.-]+/?\d+(?:v\d+)?)'), paper),
)
