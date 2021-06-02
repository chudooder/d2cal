from bs4 import BeautifulSoup
import requests

class Event:
  def __init__(self, title, matches):
    self.title = title
    self.matches = matches

class Match:
  def __init__(self, stage, round, timestamp, team1, team2, num_games):
    self.stage = stage
    self.round = round
    self.timestamp = int(timestamp)
    self.team1 = team1
    self.team2 = team2
    self.num_games = num_games
    self.end_timestamp = self.num_games * 60 * 60 + self.timestamp

  def get_key(self):
    return conform_str('{}|{}|{}'.format(self.stage, self.round, self.index))

  def get_summary(self):
    return f'{self.team1} vs {self.team2} - {self.stage} / {self.round}'

def conform_str(string):
  return string.lower().replace(' ', '')

def get_match(popup):
  bracket_column = popup.find_parent(class_='bracket-column')
  tbody = popup.find_parent('tbody')
  headline = popup.find_previous('h2').find(class_='mw-headline')

  left_team = popup.find(class_='bracket-popup-header-left').get_text()
  right_team = popup.find(class_='bracket-popup-header-right').get_text()
  timestamp = popup.find(class_='timer-object')['data-timestamp']
  num_games = len(popup.find_all(class_='bracket-popup-body-match'))

  if bracket_column != None:
    bracket_header = bracket_column.find(class_='bracket-header')
    return Match(headline.string, bracket_header.string, timestamp, left_team, right_team, num_games)

  elif tbody != None:
    th = tbody.find('th')
    return Match(headline.string, th.string, timestamp, left_team, right_team, num_games)

def parse_event(url):
  res = requests.get(url)
  soup = BeautifulSoup(res.text, features='lxml')

  title = soup.find('h1', id='firstHeading').get_text()

  popups = soup.find_all(class_='bracket-popup')
  matches = {}

  i = 0
  current_stage_round = ""
  for popup in popups:
    match = get_match(popup)
    if match.stage + match.round != current_stage_round:
      current_stage_round = match.stage + match.round
      i = 0
    match.index = i
    i += 1
    matches[match.get_key()] = match

  return Event(title, matches)