from flask import Flask, render_template, url_for, request, redirect
import requests
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../libs/python'))
from flask_utils.port_finder import find_available_port
from flask_bootstrap import Bootstrap
from flask_fontawesome import FontAwesome
from flask_sslify import SSLify

app = Flask(__name__)
if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)
Bootstrap(app)
fa = FontAwesome(app)

@app.route('/')
def index():
	error = request.args.get('error')
	return render_template('weather.html', weather=None, error=error)

@app.route('/weather')
def weather():
	try:
		city = request.args.get('city')
		state = request.args.get('state')
		country = request.args.get('country')
		unit = request.args.get('unit')
		if state:
			req = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city},{state},{country}&units={unit}&appid=da0cf3bb954fb7fd96d7095ca8c4cb5f').json()
		else:
			req = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city},{country}&units={unit}&appid=da0cf3bb954fb7fd96d7095ca8c4cb5f').json()
		weather = req['weather'][0]
		temp = req['main']
		return render_template('weather.html', weather=weather, temp=temp, unit=unit, error=None)
	except:
		return render_template('weather.html', weather=None, error="Looks like we couldn't find the place you were looking for. Please check to make sure you put things in the right field and that your spelling is correct.")

@app.route('/get_weather', methods=['POST'])
def get_weather():
	city = request.form['city']
	state = request.form['state']
	country = request.form['country']
	unit = request.form['unit-type']
	return redirect(url_for('weather', city=city, country=country, state=state, unit=unit))


if __name__ == '__main__':
    try:
        port = find_available_port(3000, 3100)
        print(f"Starting Flask app on port {port}")
        app.run(threaded=True, debug=True, port=port)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
