from google.oauth2 import service_account
import googleapiclient.discovery

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'd2cal-315518-7fab0d0b0962.json'

def get_calendar_client():
  credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
  calendar = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
  return calendar

def get_firestore_client():
  if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {
      'projectId': 'd2cal-315518'
    })
  return firestore.client()