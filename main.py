
import os
from flask import Flask , render_template, jsonify, request, redirect, url_for
from scrapy.crawler import CrawlerRunner

import time
import subprocess
import json
import re
# Importing our Scraping Function from the amazon_scraping file

from request100.spiders.moviespider import StagaSpider


# Creating Flask App Variable

app = Flask(__name__)
app.debug = True
output_data = []
crawl_runner = CrawlerRunner()
sea= ""


def get_results():
    results = ['staga']
    data = []
    for result in results: 
        with open(f'{result}.json', encoding='utf-8') as data_file:
            data += json.loads(re.sub(r'("(?:\\?.)*?")|,\s*([]}])', r'\1\2', data_file.read()))
    return data

# By Deafult Flask will come into this when we run the file
@app.route('/')
def index():
    return render_template("index.html") # Returns index.html file in templates folder.


@app.route('/about', methods=['GET',])
def about():
    return render_template("about.html") # Returns index.html file in templates folder.

# After clicking the Submit Button FLASK will come into this
@app.route('/', methods=['POST'])
def submit():
    if request.method == 'POST':
        s = request.form['searchText'] # Getting the Input Amazon Product URL
        if s == None:
            return redirect(url_for('index'))
        global baseURL
        baseURL = s
        sea = baseURL
        print(os.getcwd())
        # This will remove any existing file with the same name so that the scrapy will not append the data to any previous file.
        return redirect(url_for('scrape')) # Passing to the Scrape function


@app.route("/scrape")
def scrape():
    print(os.getcwd())
    spider_name = "staga"
    print(subprocess.check_output(['scrapy', 'crawl', spider_name, '-a', f'search_text="{baseURL}"']))
    return redirect(url_for('result'))


@app.route('/result', methods=['GET',])
def result():
    title='Result - '
    data = get_results()
    return render_template("result.html", searchText=sea,title=title,data=data) # Returns index.html file in templates folder.












if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", default=5000),host=os.getenv("HOST", default="0.0.0.0"))
   
