import requests
import json
import time
from playsound import playsound
from flask import session, request
from flask_socketio import SocketIO, send, emit

base_url = "https://statsapi.web.nhl.com"


def get_game(team_id, room):
	try: # get game status if it exists - IndexError == no game -> send to client
		game_status = get_game_status(team_id)
		emit('status', game_status, room=room)
		game = True
	except IndexError:
		emit('status', f"The {session['team_name']} do not play today.", room=room)
		game = False

	return game


def get_teams(data, room):
	try: 
		away_team = data['dates'][0]['games'][0]['teams']['away']['team']['name']
		home_team = data['dates'][0]['games'][0]['teams']['home']['team']['name']
		emit('teams', (away_team, home_team), room=room)
	except IndexError:
		emit('teams', ('N/A', 'N/A'), room=room)


def get_team(abr):
	r = requests.get(base_url + "/api/v1/teams")
	data = r.json()
		
	for team in data['teams']:
		if team['abbreviation'] == abr:
			team_id = team['id']

			return team_id


def get_data(team_id):
	r = requests.get(base_url + f"/api/v1/schedule?teamId={team_id}&expand=schedule.linescore")
	data = r.json()

	# with open("sched.json", "r") as f:
	# 	data = json.load(f) # for testing

	return data


def get_game_status(team_id):
	data = get_data(team_id)
	game_status = data['dates'][0]['games'][0]['status']['abstractGameState']

	return game_status


def celebration(abr):
	"""celebration when the your team scores."""
	try:
		playsound(f"static/sounds/{abr}.mp3")
	except NameError:
		playsound("static/sounds/goal.mp3")


def win(abr):
	"""celebration to play when your team wins"""
	try:
		playsound(f"static/sounds/{stl}_win.mp3")
	except NameError:
		playsound("static/sounds/win.mp3")

def watchgame(abr, stream_delay, room):
	team_id = get_team(abr)

	game = get_game(team_id, room)
	data = get_data(team_id)
	get_teams(data, room)

	game_status = data['dates'][0]['games'][0]['status']['abstractGameState']

	if game:
		home = False
		away = False
		away_teamId = data['dates'][0]['games'][0]['teams']['away']['team']['id']
		home_teamId = data['dates'][0]['games'][0]['teams']['home']['team']['id']
		if home_teamId == team_id: # set home or away for the team you picked
			home = True
		if away_teamId == team_id:
			away = True

	while game:
		emit('status', game_status, room=room)
		game_status = get_game_status(team_id)
		if game_status == "Preview":
			time.sleep(15)
			# pass

		if game_status == "Live":
			i = 0
			while game_status == "Live":
				"""Continous loop to check game score, play cellys"""
				emit('status', (game_status), room=room) # update game status on client

				data = get_data(team_id)
				game_status = data['dates'][0]['games'][0]['status']['abstractGameState']

				# set new scores with new data
				away_score = data['dates'][0]['games'][0]['teams']['away']['score']
				home_score = data['dates'][0]['games'][0]['teams']['home']['score']

				emit('scores', (away_score, home_score), room=room) # scores -> client

				if i == 1: # skip on first iteration to set comparison scores
					if away:
						if away_score != away_scoreLast:
							time.sleep(stream_delay)
							emit('goal', room=room)
							celebration(abr)
							emit('goalover', room=room)
					if home:
						if home_score != home_scoreLast:
							time.sleep(stream_delay)
							emit('goal', room=room)
							emit(celebration(abr), room=room)
							emit('goalover', room=room)
				else:
					i += 1 # set i equal to 1 on first iteration

				# set last loop's scores to compare against
				away_scoreLast = away_score
				home_scoreLast = home_score

				time.sleep(5) # request every x seconds
				# END WHILE TRUE LOOP #

		if game_status == "Final":
			emit('status', game_status, room=room)
			
			if away:
				if away_score > home_score:
					time.sleep(stream_delay)
					win(abr) # PLAY GLORIA!
			if home:
				if home_score > away_score:
					time.sleep(stream_delay)
					win(abr)			
			break