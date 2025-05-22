from quart import Quart, render_template
from datastar_py.sse import ServerSentEventGenerator as SSE
from datastar_py.quart import make_datastar_response

import asyncio
from random import random
import json


# CONFIG

app = Quart(__name__)
app.secret_key = 'a_secret_key'

STONKS_1 = [round(random()*90) for _ in range(10)]
STONKS_2 = [round(random()*90) for _ in range(10)]

# UTILS

async def get_stonks():
    global STONKS_1, STONKS_2
    while True:
        new_stonk = round(random()*90)
        STONKS_1 = STONKS_1[1:] + [new_stonk]
        new_stonk = round(random()*90)
        STONKS_2 = STONKS_2[1:] + [new_stonk]
        await asyncio.sleep(2)

async def make_path(stonks):
    path = f"M0,{100-stonks[0]}"
    for n, stonk in enumerate(stonks):
        path += f" L{n*10},{100-stonk}"
    return path

# VIEWS

async def defs_change():
    path_1 = await make_path(STONKS_1)
    circle_1 = {'x': 90, 'y': 100-STONKS_1[-1]}
    path_2 = await make_path(STONKS_2)
    circle_2 = {'x': 90, 'y': 100-STONKS_2[-1]}
    text_data = ["buy data!", "var(--primary)"] if STONKS_1[-1] < STONKS_2[-1] else ["buy stars!", "var(--secondary)"]
    if STONKS_1[-1] == STONKS_2[-1]:
        text_data = ["PANIC!§ SELL!! PANIC!!", "red"] 
    html = f'''
<svg id="defs">
<defs>
<g id="left">
    <g
    fill=none stroke-width=1
    vector-effect=non-scaling-stroke>
        <path d="{path_1}" stroke=var(--primary) />
        <circle cx={circle_1["x"]} cy={circle_1["y"]} r=1 fill=var(--primary) />
        <path d="{path_2}" stroke=var(--secondary) />
        <circle cx={circle_2["x"]} cy={circle_2["y"]} r=1 fill=var(--secondary) />
        <text x=50% y=8 fill={text_data[1]}>{text_data[0]}</text>
    </g>
</g>
</defs>
</svg>
    '''
    return html

async def get_echarts_data():
    global STONKS_1, STONKS_2
    gauge_data = [
        {
            "value": STONKS_1[-1],
            "name": "DATA",
            "title": {
                "offsetCenter": ["0%", "-30%"]
            },
            "detail": {
                "valueAnimation": True,
                "offsetCenter": ["0%", "-20%"]
            }
        },
        {
            "value": STONKS_2[-1],
            "name": "STARS",
            "title": {
                "offsetCenter": ["0%", "0%"]
            },
            "detail": {
                "valueAnimation": True,
                "offsetCenter": ["0%", "10%"]
            }
        }
    ]
    return json.dumps(gauge_data)

# APP

@app.before_serving
async def before_serving():
    asyncio.create_task(get_stonks())

@app.get('/')
async def index():
    return await render_template('index.html')

@app.get('/defs')
async def defs():
    async def event():
        while True:
            try:
                html = await defs_change()
                yield SSE.merge_fragments(fragments=[html])
                gauge_data = await get_echarts_data()
                yield SSE.execute_script(
                    script=f"myChart.setOption({{series: [{{data: {gauge_data}, pointer: {{show: false}}}}]}});"
                )
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
    return await make_datastar_response(event())

if __name__ == '__main__':
    app.run(debug=True)
