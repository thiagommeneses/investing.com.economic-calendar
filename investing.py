import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import arrow


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'


class Good():
	def __init__(self):
		self.value = "+"
		self.name = "good"

	def __repr__(self):
		return "<Good(value='%s')>" % (self.value)


class Bad():
	def __init__(self):
		self.value = "-"
		self.name = "bad"

	def __repr__(self):
		return "<Bad(value='%s')>" % (self.value)


class Unknow():
	def __init__(self):
		self.value = "?"
		self.name = "unknow"

	def __repr__(self):
		return "<Unknow(value='%s')>" % (self.value)


class InvestingCom():
	"""Parse the economic calendar published at investing.com.

	Note: investing.com returns HTTP 403 for every request coming from
	some networks/IP ranges (confirmed from this environment), but works
	fine from others. `Investing` uses this class as the primary source
	and automatically falls back to `TradingEconomics` when it fails.
	"""

	def __init__(self, uri='https://br.investing.com/economic-calendar/'):
		self.uri = uri
		self.req = urllib.request.Request(uri)
		self.req.add_header('User-Agent', USER_AGENT)
		self.result = []

	def news(self):
		response = urllib.request.urlopen(self.req, timeout=10)
		html = response.read()

		soup = BeautifulSoup(html, "html.parser")

		table = soup.find('table', {"id": "economicCalendarData"})
		tbody = table.find('tbody')
		rows = tbody.find_all('tr', {"class": "js-event-item"})

		for tr in rows:
			news = {'timestamp': None,
					'country': None,
					'url': None,
					'name': None,
					'bold': None,
					'fore': None,
					'prev': None,
					'signal': None}

			_datetime = tr.attrs.get('data-event-datetime')
			if _datetime:
				try:
					news['timestamp'] = arrow.get(_datetime, "YYYY/MM/DD HH:mm:ss").timestamp()
				except arrow.parser.ParserError:
					pass

			flag_cell = tr.find('td', {"class": "flagCur"})
			flag = flag_cell.find('span') if flag_cell else None
			news['country'] = flag.get('title') if flag else None

			event_cell = tr.find('td', {"class": "event"})
			link = event_cell.find('a') if event_cell else None
			if link:
				news['url'] = urljoin(self.uri, link.get('href', ''))
				news['name'] = link.get_text(strip=True)

			bold = tr.find('td', {"class": "bold"})
			news['bold'] = bold.get_text(strip=True) if bold else ''

			fore = tr.find('td', {"class": "fore"})
			news['fore'] = fore.get_text(strip=True) if fore else ''

			prev = tr.find('td', {"class": "prev"})
			news['prev'] = prev.get_text(strip=True) if prev else ''

			bold_classes = bold.get('class', []) if bold else []
			if 'redFont' in bold_classes:
				news['signal'] = Bad()
			elif 'greenFont' in bold_classes:
				news['signal'] = Good()
			else:
				news['signal'] = Unknow()

			self.result.append(news)

		return self.result


class TradingEconomics():
	"""Parse the equivalent economic calendar published at
	tradingeconomics.com. Used as a fallback when investing.com is
	unreachable.
	"""

	BASE_URL = 'https://pt.tradingeconomics.com'

	def __init__(self, uri=None, country=None, importance=None):
		"""
		uri: full calendar URL to scrape. When omitted it is built from
			`country` and `importance`.
		country: optional country slug (e.g. 'brazil', 'united-states')
			to fetch a single country's calendar
			(https://pt.tradingeconomics.com/<country>/calendar).
		importance: optional impact filter, only supported on the
			all-countries calendar (i.e. when `country` is not set):
			'1' (low), '2' (medium) or '3' (high impact).
		"""
		if uri is None:
			path = '/{}/calendar'.format(country) if country else '/calendar'
			uri = urljoin(self.BASE_URL, path)
			if importance and not country:
				uri = '{}?importance={}'.format(uri, importance)

		self.uri = uri
		self.req = urllib.request.Request(uri)
		self.req.add_header('User-Agent', USER_AGENT)
		self.result = []

	def news(self):
		response = urllib.request.urlopen(self.req, timeout=10)
		html = response.read()

		soup = BeautifulSoup(html, "html.parser")

		# Find event item rows. Nested tables (flags, sparkline
		# charts) are skipped because their <tr> have no data-url.
		table = soup.find('table', {"id": "calendar"})
		rows = table.find_all('tr', attrs={"data-url": True})

		for tr in rows:
			news = {'timestamp': None,
					'country': None,
					'url': None,
					'name': None,
					'bold': None,
					'fore': None,
					'prev': None,
					'signal': None}

			cells = tr.find_all('td', recursive=False)
			date_cell, country_cell, event_cell, actual_cell, prev_cell = cells[0:5]

			# Date comes from the cell class (e.g. "2026-09-08"),
			# time from the text inside it (e.g. "12:30 AM").
			date = next(iter(date_cell.get('class', [])), None)
			time = date_cell.get_text(strip=True)
			if date and time:
				try:
					news['timestamp'] = arrow.get("{} {}".format(date, time), "YYYY-MM-DD h:mm A").timestamp()
				except arrow.parser.ParserError:
					pass

			flag = country_cell.find('div', {"class": "flag"})
			news['country'] = flag.get('title') if flag else tr.get('data-country')

			news['url'] = urljoin(self.BASE_URL, tr.get('data-url', ''))

			link = event_cell.find('a', {"class": "calendar-event"})
			news['name'] = link.get_text(strip=True) if link else tr.get('data-event')

			actual = actual_cell.find(id='actual')
			news['bold'] = actual.get_text(strip=True) if actual else ''

			prev = prev_cell.find(id='previous')
			news['prev'] = prev.get_text(strip=True) if prev else ''

			forecast_cell = cells[6] if len(cells) > 6 else None
			forecast = forecast_cell.find(id='forecast') if forecast_cell else None
			news['fore'] = forecast.get_text(strip=True) if forecast else ''

			actual_classes = actual_cell.get('class', [])
			if 'calendar-item-positive' in actual_classes:
				news['signal'] = Good()
			elif 'calendar-item-negative' in actual_classes:
				news['signal'] = Bad()
			else:
				news['signal'] = Unknow()

			self.result.append(news)

		return self.result


class Investing():
	"""Parse the economic calendar, preferring investing.com and
	automatically falling back to tradingeconomics.com when
	investing.com can't be reached (e.g. HTTP 403).
	"""

	def __init__(self, uri=None, country=None, importance=None):
		"""
		uri: full investing.com calendar URL to try first (passed to
			`InvestingCom`). Ignored by the tradingeconomics.com fallback.
		country, importance: passed to the `TradingEconomics` fallback,
			see its docstring.
		"""
		self.uri = uri
		self.country = country
		self.importance = importance

	def news(self):
		try:
			investing_com = InvestingCom(self.uri) if self.uri else InvestingCom()
			result = investing_com.news()
			if result:
				return result
		except Exception as error:
			# Covers HTTP errors (e.g. the 403 investing.com returns from
			# some networks) as well as parsing failures if its markup
			# has changed since this was last verified against the live
			# site.
			print("investing.com indisponivel ({}), usando tradingeconomics.com".format(error))

		return TradingEconomics(country=self.country, importance=self.importance).news()


if __name__ == "__main__":
	i = Investing(country='brazil')
	print(i.news())
