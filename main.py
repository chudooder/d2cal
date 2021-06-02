import matchparser
import auth

import base64
import sys
from datetime import datetime, timezone
import dateutil.parser
import re
import time

def get_calendar_doc(firestore, url):
  return firestore.collection('calendars').document(get_key_from_url(url))

def get_key_from_url(url):
  i = url.index('liquipedia.net/')
  key = url[i + len('liquipedia.net/'):]
  return key.replace('/', '|')

def get_unix_time_from_iso(iso):
  return int(dateutil.parser.parse(iso).timestamp())

def get_key_from_event(event):
  return event['description']

def create_calendar(firestore, gcal, url, summary):
  calendar = {
    'summary': summary,
    'timeZone': 'America/Los_Angeles'
  }

  created_calendar = gcal.calendars().insert(body=calendar).execute()
  get_calendar_doc(firestore, url).set({
    'id': created_calendar['id']
  })
  return created_calendar['id']

def create_calendar_acls(gcal, calendar_id):
  rule = {
    'role': 'reader',
    'scope': {
      'type': 'default'
    }
  }
  rule = gcal.acl().insert(calendarId=calendar_id, body=rule).execute()
  return rule['id']

def clear_calendar(gcal, calendar_id):
  events = gcal.events().list(calendarId=calendar_id).execute()
  for event in events['items']:
    gcal.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
  print('Cleared calendar')

def event_has_delta(old_event, new_event):
  if new_event['summary'] != old_event['summary']:
    return True

  new_start = get_unix_time_from_iso(new_event['start']['dateTime'])
  old_start = get_unix_time_from_iso(old_event['start']['dateTime'])

  if new_start != old_start:
    return True

  new_end = get_unix_time_from_iso(new_event['end']['dateTime'])
  old_end = get_unix_time_from_iso(old_event['end']['dateTime'])

  if new_end != old_end:
    return True

  return False

def upsert_calendar_event(gcal, calendar_id, existing_events_map, match):
  start = datetime.fromtimestamp(match.timestamp, tz=timezone.utc).astimezone().isoformat()
  end = datetime.fromtimestamp(match.end_timestamp, tz=timezone.utc).astimezone().isoformat()
  event = {
    'summary': match.get_summary(),
    'start': {
      'dateTime': start
    },
    'end': {
      'dateTime': end
    },
    'description': match.get_key()
  }

  if match.get_key() in existing_events_map:
    event_id = existing_events_map[match.get_key()]['id']
    if event_has_delta(existing_events_map[match.get_key()], event):
      print('Existing event found with id ' + event_id + ', updating')
      event = gcal.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    else:
      print('Existing event found with id ' + event_id + ' but no changes found, skipping')
  else:
    event = gcal.events().insert(calendarId=calendar_id, body=event).execute()
  

def pubsub_main(event, context):
  pubsub_message = base64.b64decode(event['data']).decode('utf-8')
  main(pubsub_message)

def main(url):
  gcal = auth.get_calendar_client()
  firestore = auth.get_firestore_client()

  print('Parsing event from ' + url)
  event = matchparser.parse_event(url)
  matches = event.matches

  doc = get_calendar_doc(firestore, url).get()

  if doc.exists:
    calendar_id = doc.to_dict()['id']
    print('Calendar exists with id ' + calendar_id)
  else:
    print('Calendar does not exist, creating...')
    calendar_id = create_calendar(firestore, gcal, url, event.title)
    print('Created calendar with id: ' + calendar_id)
    acl_id = create_calendar_acls(gcal, doc.to_dict()['id'])
    print('Created access control list with id: ' + acl_id)

  existing_events = gcal.events().list(calendarId=calendar_id).execute()['items']
  existing_events_map = {get_key_from_event(event): event for event in existing_events}

  for match_key, match in matches.items():
    upsert_calendar_event(gcal, calendar_id, existing_events_map, match)

if __name__ == '__main__':
  main(sys.argv[1])