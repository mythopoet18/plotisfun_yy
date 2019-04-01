from flask import Flask,render_template,request,redirect
import pandas as pd
import requests
import simplejson as json
from requests_oauthlib import OAuth1

from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource,LinearAxis, Range1d,Band,HoverTool,NumeralTickFormatter
from bokeh.io import curdoc, reset_output
from bokeh.embed import components
from bokeh.resources import INLINE, CDN

from math import pi

app = Flask(__name__)

app.vars={}

with open("secrets/alphavantage_secrets.json.nogit") as f:
    secrets = json.loads(f.read())
# create an auth object
auth = OAuth1(
    secrets["apikey"]
)

def dailystock(symbol):
            params={'function':'TIME_SERIES_DAILY',
            'symbol':symbol,
            'output':'compact',
            'apikey': auth}
            return requests.get('https://www.alphavantage.co/query',
                        params=params)

def keywordsearch(keywords):
            params={'function':'SYMBOL_SEARCH',
            'keywords':keywords,
            'output':'compact',
            'apikey': auth}
            return requests.get('https://www.alphavantage.co/query',
                        params=params)

@app.route('/index',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template('lookup_yy.html')
    else:
        #user submit keyword searchTerm
        app.vars['kw_yy']=request.form['kw_yy']

        kw0=keywordsearch(app.vars['kw_yy'])
        #kw0=requests.get('https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=Micro&apikey=demo')

        kw1=kw0.json()
        with open('kw-suggestion.json','w') as kw:
            json.dump(kw1['bestMatches'],kw)
        with open('kw-suggestion.json','r') as kw:
            kws=pd.read_json(kw)

        if len(kws.index)==1:
            app.vars['symbol']=request.form['kw_yy'].upper()
            return redirect('main_yy')
        elif len(kws.index)==0:
            return render_template('lookup_yy.html')
        else:
            kws1=kws['1. symbol']
            kws2=list(kws1)
            ti='\n'.join(kws2)
        return render_template('lookup_kw_yy.html',tickers=ti)

@app.route('/kw',methods=['POST'])
def kw():
    app.vars['symbol']=request.form['symbol_yy'].upper()
    return redirect('main_yy')

@app.route('/main_yy',methods=['GET'])
def main_yy():
    dp=dailystock(app.vars['symbol'])
#    dp=requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo')
    dp1=dp.json()

    with open('meta_temp.json','w') as temp:
        json.dump(dp1['Meta Data'],temp)
    with open('ts_temp.json','w') as temp1:
        json.dump(dp1['Time Series (Daily)'],temp1)

    with open('ts_temp.json','r') as dp1:
        df=pd.read_json(dp1)
        t2=df.T

# manipulate dataframe
    tavg=(t2['2. high']+t2['3. low'])/2
    ma0=tavg.rolling(20).median()
    std0=tavg.rolling(20).std()

    ma1=ma0[19:-1].copy()
    ma1.index=t2.index[:-20]
    std1=std0[19:-1].copy()
    std1.index=t2.index[:-20]

    blg_upper=ma1+std1*2
    blg_lower=ma1-std1*2

    t2['avg']=tavg
    t3=t2[:-20].copy()
    t3['blg_upper']=blg_upper
    t3['blg_lower']=blg_lower
    t3['ma']=ma1

# use bokeh Plotting
    reset_output()
    aha=ColumnDataSource(t3)
# create plot 1
    inc = t3['4. close'] > t3['1. open']
    dec = t3['4. close'] < t3['1. open']
    w = 12*60*60*1000 # 100 day in ms

    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
    p = figure(x_axis_type="datetime", tools=TOOLS,toolbar_location="left",
               plot_width=800,plot_height=400,sizing_mode='scale_width',
               title="%s Candlestick plot with Bollinger Band"%(app.vars['symbol']))
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00 a")
    p.xaxis.major_label_orientation = pi/4
    p.grid.grid_line_alpha=0.3
    p.title.text_color = "olive"

    p.segment(t3.index, t3['2. high'], t3.index, t3['3. low'], color="black")
    p.vbar(t3.index[inc], w, t3['1. open'][inc], t3['4. close'][inc], fill_color="#D5E1DD", line_color="black")
    p.vbar(t3.index[dec], w, t3['1. open'][dec], t3['4. close'][dec], fill_color="#F2583E", line_color="black")
    p.line(x='index',y='ma',source=aha,line_color="darkslateblue",legend='Moving Average')

    band = Band(base='index', lower='blg_lower', upper='blg_upper', source=aha, level='underlay',
                fill_alpha=0.3, fill_color='lavender', line_width=1, line_color='orange')
    p.add_layout(band)

    hover_cs=HoverTool(tooltips=[('Date','$x{%Y-%m-%d}'),
                                 ('Open($)','@{1. open}{0,0.0 }'),
                                 ('Close($)','@{4. close}{0,0.0 }')
                                 ],
                              formatters={'$x': 'datetime'},
                              mode='vline')
    p.add_tools(hover_cs)

    p.legend.location = "bottom_right"

# create plot 2
    ahas=ColumnDataSource(t3)

    s1 = figure(x_axis_type="datetime",
                tools=TOOLS, toolbar_location="left",
                plot_width=800,plot_height=400,sizing_mode='scale_width',
                title="%s Daily Average Price and Transaction Volume"%(app.vars['symbol']))
    s1.yaxis[0].formatter = NumeralTickFormatter(format="$0.00 a")
    s1.y_range = Range1d(t3['avg'].min()/1.5, t3['avg'].max()*1.2)
    s1.extra_y_ranges = {"vol": Range1d(start=t3['5. volume'].min(), end=t3['5. volume'].max()*2)}
    s1.title.text_color = "olive"
    s1.legend.click_policy="mute"

    s1.add_layout(LinearAxis(y_range_name="vol",formatter = NumeralTickFormatter(format="0.00 a")), 'right')
    price=s1.line(x='index',y='avg', source=ahas,
                  line_color="darkslateblue",line_width=1,
                  legend='Average Daily Price')

    volume=s1.line(x='index',y='5. volume',source=ahas,
                   line_color="sienna",line_width=2,
                   legend='Daily Trading Volumn',
                   y_range_name="vol")

    hover_price=HoverTool(tooltips=[( 'Date','$x{%Y-%m-%d}'),('Price($)','@avg{0,0.0 }')],
                          formatters={'$x': 'datetime'},
                          mode='vline',renderers=[price])

    hover_volume=HoverTool(tooltips=[( 'Date','$x{%Y-%m-%d}'),( 'Volume','@{5. volume}{0.00 a}')],
                           formatters={'$x': 'datetime'},
                           mode='vline',renderers=[volume])

    s1.add_tools(hover_price)
    s1.add_tools(hover_volume)
# generate multiple plot handler
    script1, div1 = components(p)
    script2, div2 = components(s1)

# get components
#    script, div = components([p,s1])
    cdn_js=CDN.js_files[0]
    cdn_css=CDN.css_files[0]

    return render_template('plotting_yy.html',
                           script1=script1,script2=script2,
                           div1=div1,div2=div2,
                          # script=script,div=div,
                           cdn_css=cdn_css,
                           cdn_js=cdn_js,
                           symbol=app.vars['symbol'])

if __name__ == '__main__':
  app.run()
 # app.run(debug=True)
