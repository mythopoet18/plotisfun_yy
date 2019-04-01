## Plotting Daily Stock Price with Bokeh

The home page provides a `keyword search` function to help users find the stock ticker. The `ticker search` page asks users to type the desired stock ticker. The `plotting page` renders two plots.

## API

The data source is `Alphavantage`. Free users can make up to 500 requests per day. The web app applies the `daily stock price` and `end point search` functions. 

`daily stock price` contains the following information
<ul>
  <li>Open price </li>
  <li>Close price </li>
  <li>High </li>
  <li>Low </li>
  <li>Volume </li>
</ul>

`end point search` contains a list of suggested tickers

## Bokeh and Pandas

I use `pandas` dataframe to manipulate the time series data, generating `average daily price`, `moving average` and `Bollinger bands`. Then generate two plots using `bokeh`:

<ul>
  <li>The candlestick plot with Bollinger bands</li>
  <li>The average daily stock price and transaction volume</li>
</ul>

The plot has interactive hover tool. The second plot use twin y-axis to show different metrics.

The two plots are imbedded to the plotting template using components.

## Tabs
The home
