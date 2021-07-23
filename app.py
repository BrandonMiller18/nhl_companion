import os
import json
import time
import requests
from playsound import playsound
from flask import Flask, redirect, url_for, render_template, request, session, flash, send_from_directory
from flask_socketio import SocketIO, send, emit

from goal_horn import *


app = Flask(__name__)
app.config.from_pyfile('config.py')
socketio = SocketIO(app)

base_url = "https://statsapi.web.nhl.com"

@socketio.on('message')
def handle_message(msg):
	stream_delay = int(msg)
	abr = session['abr']
	room = request.sid
	print("Session ID: " + room, flush=True)

	watchgame(abr, stream_delay, room)



@app.route("/", methods=["POST", "GET"])
def home():
	r = requests.get(base_url + "/api/v1/teams")
	teams = r.json()
	teams = teams["teams"]
	abbreviations = []
	i = 0
	for team in teams:
		abbreviations.append(teams[i]['abbreviation'])
		i += 1

	r = requests.get(base_url + "/api/v1/schedule")
	schedule = r.json()
	
	try:
		date = schedule["dates"][0]["date"]
		schedule = schedule["dates"][0]["games"]
	except:
		date = "No Games"
		schedule = "No Games"

	r = requests.get(base_url + "/api/v1/standings")
	standings = r.json()
	standings = standings["records"]

	divisions = []
	team_stats = []

	x = 0
	for record in standings:
		div_name = record["division"]["name"]
		divisions.append(div_name)

		teams = standings[x]["teamRecords"]
		x+=1

		for team in teams:
			team_name = team["team"]["name"]
			team_id = team["team"]["id"]
			team_link = base_url + team["team"]["link"]
			team_wins = team["leagueRecord"]["wins"]
			team_losses = team["leagueRecord"]["losses"]
			team_ot = team["leagueRecord"]["ot"]
			team_points = team["points"]
			games_played = team["gamesPlayed"]
		
			# r = requests.get(team_link)
			# team_data = r.json()
			# website = team_data["teams"][0]["officialSiteUrl"]

			team = {
			"name" : team_name,
			"id" : team_id,
			# "link" : website,
			"wins" : team_wins,
			"losses" : team_losses,
			"ot" : team_ot,
			"pts" : team_points,
			"gp" : games_played,
			"div" : div_name
			}

			team_stats.append(team)

	return render_template("index.html",
		abbreviations=sorted(abbreviations),
		schedule=schedule,
		divisions=divisions,
		standings=team_stats,
		date=date,
		)


@app.route("/watchgame", methods=["GET", "POST"])
def run():
	domain = os.environ.get('DOMAIN')
	
	if request.method == "POST":

		abr = request.form['team']
		session['abr'] = abr # set team abbreviation
		horn = domain + f"static/sounds/{abr.lower()}.mp3"
		win = domain + f"static/sounds/{abr.lower()}_win.mp3"
		generic_win = domain + "static/sounds/win.mp3"

		r = requests.get(base_url + "/api/v1/teams")
		teams = r.json()
		teams = teams["teams"]

		for team in teams: # set match to abbreviation to get team name
			team_name = team["name"]
			if team["abbreviation"] == abr:
				session['team_name'] = team_name
				break

		return render_template(
			"app.html",
			name=session['team_name'],
			horn=horn,
			win=win,
			genericWin = generic_win,
			domain=domain,
			)
	else:
		if 'abr' in session and 'team_name' in session:
			abr = session['abr']
			horn = domain + f"static/sounds/{abr.lower()}.mp3"
			win = domain + f"static/sounds/{abr.lower()}_win.mp3"
			generic_win = domain + "static/sounds/win.mp3"
			return render_template(
				"app.html",
				name=session['team_name'],
				horn=horn,
				win=win,
				genericWin = generic_win,
				domain=domain,
				)

		else:
			flash("Please select a team before continuing to the app!",
				"text-center alert alert-info mt-2 mr-2")
			return redirect(url_for("home"))


@app.route("/about")
def about():
	return render_template("about.html")

# sitemap
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == '__main__':
	socketio.run(app)