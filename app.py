import os
import json
import time
import requests
from playsound import playsound
from flask import Flask, redirect, url_for, render_template, request, session, flash
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
	abbreviations = r.json()
	abbreviations = abbreviations["teams"]

	r = requests.get(base_url + "/api/v1/schedule")
	schedule = r.json()
	schedule = schedule["dates"][0]["games"]

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
			team_wins = team["leagueRecord"]["wins"]
			team_losses = team["leagueRecord"]["losses"]
			team_ot = team["leagueRecord"]["ot"]
			team_points = team["points"]
			games_played = team["gamesPlayed"]

			team = {
			"name" : team_name,
			"wins" : team_wins,
			"losses" : team_losses,
			"ot" : team_ot,
			"pts" : team_points,
			"gp" : games_played,
			"div" : div_name
			}

			team_stats.append(team)

	return render_template("index.html",
		abbreviations=abbreviations,
		schedule=schedule,
		divisions=divisions,
		standings=team_stats
		)


@app.route("/watchgame", methods=["GET", "POST"])
def run():
	if request.method == "POST":

		abr = request.form['team']
		session['abr'] = abr # set team abbreviation

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
			)
	else:
		if 'abr' in session and 'team_name' in session:
			return render_template(
				"app.html",
				name=session['team_name'])

		else:
			flash("Please select a team before continuing to the app!",
				"text-center alert alert-info mt-2 mr-2")
			return redirect(url_for("home"))

if __name__ == '__main__':
	socketio.run(app)