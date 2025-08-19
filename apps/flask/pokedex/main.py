from flask import Flask, render_template, url_for, request, redirect
import requests
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../libs/python'))
from flask_utils.port_finder import find_available_port
from flask_bootstrap import Bootstrap
from flask_fontawesome import FontAwesome
import json
from flask_sslify import SSLify

app = Flask(__name__)
if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)
Bootstrap(app)
fa = FontAwesome(app)

@app.route('/')
def index():
	pokemon = [" ".join(i["name"].split("-")).title() for i in requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit=-1').json()["results"]]
	return render_template('index.html', pokemon=pokemon)

@app.route('/<pokemon>')
def pokemon(pokemon):
	try:
		req = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon}').json()
		print(req["id"])
		stats = req['stats']
		types = req['types']
		sprites = [req['sprites'][i] for i in req['sprites']]
		name = " ".join(req['name'].split("-")).title()
		weight = req['weight']
		sprites[0], sprites[1], sprites[2], sprites[3], sprites[4], sprites[5], sprites[6], sprites[7] = sprites[4], sprites[0], sprites[5], sprites[1], sprites[6], sprites[2], sprites[7], sprites[3]
		sprites = [i if i != None else "" for i in sprites]
		return render_template('pokemon.html', stats=stats, types=types, sprites=sprites, name = name, weight = weight)
	except:
		return redirect(url_for('index'))

@app.route('/get_pokemon', methods=['POST'])
def get_pokemon():
	try:
		pokemon = request.form['pokemon']
		pk = "-".join(pokemon.split(" ")).lower()
		return redirect(url_for('pokemon', pokemon=pk))
	except:
		return redirect(url_for('index'))

if __name__ == '__main__':
    try:
        port = find_available_port(3000, 3100)
        print(f"Starting Flask app on port {port}")
        app.run(threaded=True, port=port, debug=True)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

