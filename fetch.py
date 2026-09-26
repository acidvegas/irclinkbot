#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# fetch.py

try:
	import aiohttp
except ImportError:
	raise ImportError('missing aiohttp library (pip install aiohttp)')


BOT_UA     = 'irclinkbot (https://github.com/acidvegas/irclinkbot)'
BROWSER_UA = 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0'
EMBED_UA   = 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)' # Many sites only serve OpenGraph tags to link preview crawlers

MAX_BODY      = 2 * 1024 * 1024 # Max bytes to download for HTML pages
MAX_IMAGE     = 256 * 1024      # Max bytes to download for images (only the header is needed for dimensions)
MAX_REDIRECTS = 5
TIMEOUT       = 10


class Response:
	'''Result of a generic fetch'''

	def __init__(self, url: str, status: int, content_type: str, charset: str, length: int, body: bytes, complete: bool):
		self.url          = url
		self.status       = status
		self.content_type = content_type
		self.charset      = charset
		self.length       = length
		self.body         = body
		self.complete     = complete


def create_session() -> aiohttp.ClientSession:
	'''Create the shared HTTP session'''

	headers = {'User-Agent': BROWSER_UA, 'Accept-Language': 'en-US,en;q=0.9'}
	timeout = aiohttp.ClientTimeout(total=TIMEOUT)

	return aiohttp.ClientSession(headers=headers, timeout=timeout, max_line_size=32_768, max_field_size=32_768)


async def fetch(session: aiohttp.ClientSession, url: str, headers: dict = None) -> Response:
	'''
	Fetch a URL following redirects, only reading as much of the body as its content type needs

	:param session: HTTP session
	:param url: URL to fetch
	:param headers: Extra request headers
	'''

	async with session.get(url, headers=headers, max_redirects=MAX_REDIRECTS, allow_redirects=True) as response:
		stop = None

		if 'html' in response.content_type:
			limit = MAX_BODY
			stop  = b'</title>' # The title is all the generic parser needs, so stop downloading once we have it
		elif response.content_type.startswith('image/'):
			limit = MAX_IMAGE
		else:
			limit = 0

		body     = await read_body(response, limit, stop)
		complete = response.content.at_eof()
		length   = response.content_length or (len(body) if complete else None)

		return Response(str(response.url), response.status, response.content_type, response.charset, length, body, complete)


async def get_json(session: aiohttp.ClientSession, url: str, headers: dict = None, json: dict = None) -> dict | list:
	'''
	Fetch & decode a JSON API response (POST when a JSON body is given)

	:param session: HTTP session
	:param url: URL to fetch
	:param headers: Extra request headers
	:param json: JSON body to POST
	'''

	method = 'POST' if json is not None else 'GET'

	async with session.request(method, url, headers=headers, json=json) as response:
		response.raise_for_status()
		return await response.json(content_type=None)


async def get_text(session: aiohttp.ClientSession, url: str, headers: dict = None) -> str:
	'''
	Fetch a page as text

	:param session: HTTP session
	:param url: URL to fetch
	:param headers: Extra request headers
	'''

	async with session.get(url, headers=headers) as response:
		response.raise_for_status()
		return (await read_body(response, MAX_BODY * 2)).decode(response.charset or 'utf-8', 'replace')


async def read_body(response: aiohttp.ClientResponse, limit: int, stop: bytes = None) -> bytes:
	'''
	Read at most `limit` bytes from a response body, optionally stopping early once `stop` is seen

	:param response: HTTP response
	:param limit: Maximum number of bytes to read
	:param stop: Stop reading once this (lowercase) byte string appears in the body
	'''

	body = b''

	while len(body) < limit:
		if not (chunk := await response.content.read(limit - len(body))):
			break
		body += chunk
		if stop and stop in body[-len(chunk)-len(stop):].lower():
			break

	return body
