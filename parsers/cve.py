#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/cve.py

import re

from fetch      import get_json
from formatting import BLACK, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, bold, clean, color, line, site_tag


TAG      = site_tag('CVE', WHITE, BLACK)
SEVERITY = {'CRITICAL': RED, 'HIGH': ORANGE, 'MEDIUM': YELLOW, 'LOW': GREEN}


async def cve(session, match: re.Match) -> str | None:
	'''
	Parse a CVE link using the NVD API for CVSS scores, falling back to the cve.org API (no API keys required)

	:param session: HTTP session
	:param match: Regex match with the CVE id as group 1
	'''

	cve_id = match.group(1).upper()

	try:
		data    = (await get_json(session, f'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}'))['vulnerabilities'][0]['cve']
		metrics = data.get('metrics', {})
		cvss    = next((metrics[key][0]['cvssData'] for key in ('cvssMetricV40', 'cvssMetricV31', 'cvssMetricV30') if metrics.get(key)), None)
		summary = next((item['value'] for item in data.get('descriptions', []) if item['lang'] == 'en'), '')
		date    = data.get('published', '')[:10]
	except Exception:
		data    = (await get_json(session, f'https://cveawg.mitre.org/api/cve/{cve_id}'))
		cna     = data['containers']['cna']
		cvss    = None
		summary = cna.get('title') or next((item['value'] for item in cna.get('descriptions', []) if item['lang'].startswith('en')), '')
		date    = data['cveMetadata'].get('datePublished', '')[:10]

	return line(TAG,
		bold(cve_id),
		color(f'{cvss["baseScore"]} {cvss["baseSeverity"]}', SEVERITY.get(cvss['baseSeverity'], GREY)) if cvss else None,
		clean(summary, 250),
		color(date, GREY) if date else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?(?:cve\.org|nvd\.nist\.gov|cve\.mitre\.org)/.*?(CVE-\d{4}-\d{4,})', re.I), cve),
)
