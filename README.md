# investing.com.economic-calendar
The small class for parse economic calendar.

* For Python3

## Note

investing.com blocks scraping from some networks (HTTP 403, even with a
browser `User-Agent` — reproduced from this project's CI/sandbox
environment), but may still work depending on where the request comes
from. `Investing` tries investing.com first and automatically falls
back to the equivalent calendar published by
[tradingeconomics.com](https://pt.tradingeconomics.com/calendar) if
investing.com fails for any reason.

```python
from investing import Investing

# all countries, today's calendar (tries investing.com, falls back to
# tradingeconomics.com automatically)
Investing().news()

# country/importance filters only apply to the tradingeconomics.com
# fallback, since investing.com doesn't expose them as simple query
# params
Investing(country='brazil').news()
Investing(importance='3').news()
```

To use one source explicitly instead of going through the fallback
logic:

```python
from investing import InvestingCom, TradingEconomics

InvestingCom().news()
TradingEconomics(country='brazil').news()
```
