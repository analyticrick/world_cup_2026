from flask import Flask, Response

from world_cup_generate_report import DEFAULT_SHEET_ID, generate_report_html

app = Flask(__name__)


@app.route('/')
def index():
    html = generate_report_html(DEFAULT_SHEET_ID)
    return Response(html, mimetype='text/html')


@app.route('/health')
def health():
    return 'ok'
