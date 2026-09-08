# investing.com.economic-calendar
The small class for parse economic calendar.

* For Python3

## Note

investing.com now blocks scraping (every request gets HTTP 403, even
with a browser `User-Agent`), so this class scrapes the equivalent
calendar published by [tradingeconomics.com](https://pt.tradingeconomics.com/calendar)
instead.

```python
from investing import Investing

# all countries, today's calendar
Investing().news()

# single country
Investing(country='brazil').news()

# all countries, high impact events only
Investing(importance='3').news()
```
