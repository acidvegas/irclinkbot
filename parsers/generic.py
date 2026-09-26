#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/generic.py

import json
import re
import struct
import urllib.parse

from fetch      import Response
from formatting import CYAN, GREY, SEP, bold, clean, color, size, truncate


BOT_WALLS = re.compile(r'^(just a moment|attention required|access denied|please wait|are you a robot|robot check|security check|one more step|ddos-guard|verifying you are human|reddit - prove your humanity|403 forbidden|captcha)', re.I) # Anti-bot interstitial titles that are not worth posting


def image_dimensions(data: bytes) -> tuple[int, int] | None:
	'''
	Read the width & height of an image from its header bytes

	:param data: Beginning of the image file
	'''

	try:
		if data.startswith(b'\x89PNG\r\n\x1a\n'):
			return struct.unpack('>II', data[16:24])

		if data[:6] in (b'GIF87a', b'GIF89a'):
			return struct.unpack('<HH', data[6:10])

		if data.startswith(b'BM'):
			width, height = struct.unpack('<ii', data[18:26])
			return width, abs(height)

		if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
			chunk = data[12:16]
			if chunk == b'VP8 ':
				width, height = struct.unpack('<HH', data[26:30])
				return width & 0x3fff, height & 0x3fff
			if chunk == b'VP8L':
				bits = int.from_bytes(data[21:25], 'little')
				return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
			if chunk == b'VP8X':
				return int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1

		if data.startswith(b'\xff\xd8'):
			offset = 2
			while offset + 9 < len(data):
				if data[offset] != 0xff:
					offset += 1
					continue
				marker = data[offset+1]
				if 0xc0 <= marker <= 0xcf and marker not in (0xc4, 0xc8, 0xcc):
					height, width = struct.unpack('>HH', data[offset+5:offset+9])
					return width, height
				if marker == 0xd8 or 0xd0 <= marker <= 0xd7 or marker == 0xff:
					offset += 1 if marker == 0xff else 2
					continue
				offset += 2 + struct.unpack('>H', data[offset+2:offset+4])[0]

		if data[4:8] == b'ftyp' and (index := data.find(b'ispe')) != -1: # AVIF / HEIC
			return struct.unpack('>II', data[index+8:index+16])

	except struct.error:
		pass


def json_ld(text: str, kind: str) -> dict | None:
	'''
	Find the first JSON-LD object of a given @type in an HTML page

	:param text: HTML page
	:param kind: Schema.org @type to look for (Movie, Book, etc)
	'''

	for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', text, re.S | re.I):
		try:
			data = json.loads(re.sub(r'/\*.*?\*/', '', block, flags=re.S))
		except ValueError:
			continue

		for item in data if isinstance(data, list) else data.get('@graph', [data]):
			if isinstance(item, dict) and kind in (item.get('@type') if isinstance(item.get('@type'), list) else [item.get('@type')]):
				return item


def meta_tags(text: str) -> dict:
	'''
	Extract OpenGraph / meta tags from an HTML page into a dictionary

	:param text: HTML page
	'''

	tags = {}

	for tag in re.findall(r'<meta\s[^>]+>', text, re.I):
		key     = re.search(r'(?:property|name|itemprop)=["\']([^"\']+)', tag, re.I)
		content = re.search(r'content=(?:"([^"]*)"|\'([^\']*)\')', tag, re.I | re.S)
		if key and content:
			tags.setdefault(key.group(1).lower(), content.group(1) if content.group(1) is not None else content.group(2))

	return tags


def page_title(response: Response) -> str | None:
	'''
	Extract the title of an HTML page

	:param response: Fetched HTML page
	'''

	charset = response.charset

	if not charset and (match := re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', response.body[:4096], re.I)):
		charset = match.group(1).decode('ascii')

	try:
		text = response.body.decode(charset or 'utf-8', 'replace')
	except LookupError:
		text = response.body.decode('utf-8', 'replace')

	if (match := re.search(r'<title[^>]*>(.*?)</title>', text, re.I | re.S)) and (title := clean(match.group(1), 250)):
		return title

	if match := re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', text, re.I):
		return clean(match.group(1), 250)


def parse(response: Response) -> str | None:
	'''
	Build the generic output line for any link

	:param response: Fetched link
	'''

	if response.status >= 400:
		return

	url    = urllib.parse.urlparse(response.url)
	domain = color((url.hostname or '').removeprefix('www.'), GREY)
	name   = clean(urllib.parse.unquote(url.path.rsplit('/', 1)[-1]), 80)
	length = size(response.length) if response.length is not None else None

	if 'html' in response.content_type:
		if (title := page_title(response)) and BOT_WALLS.match(title):
			return
		fields = [bold(title) if title else None, length, domain]
	elif response.content_type.startswith('image/'):
		dimensions = image_dimensions(response.body)
		fields     = [name, '{}x{}'.format(*dimensions) if dimensions else None, length]
	else:
		fields = [name, length]

	return truncate(color(f'[{response.content_type or "unknown"}]', CYAN) + ' ' + SEP.join(field for field in fields if field))
