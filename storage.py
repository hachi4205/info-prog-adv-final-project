import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# TODO: replace with your own spreadsheet id and sheet/tab name
SPREADSHEET_ID = "1h1IKXd1iqwjmed9LamRZheDm9xn6Ry7qomMUkgSKpyQ"
SHEET_NAME = "Sheet1"


def _get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds).spreadsheets()

HEADERS = [
    "room_id", "host", "restaurant", "target_count", "max_participants",
    "meal_type", "deadline_minutes", "meal_time", "status",
    "participants", "menu_items", "chat_messages", "created_at",
]

def save_rooms(rooms):
    """Overwrite the whole sheet with the current rooms"""
    sheets = _get_service()

    values = [HEADERS]
    for room in rooms:
        d = room.to_dict()
        values.append([d[key] for key in HEADERS])

    sheets.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_NAME,
    ).execute()

    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def load_rooms():
    """Read all rooms from the sheet and return a list of dicts"""
    sheets = _get_service()

    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_NAME,
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        return []

    header = rows[0]
    room_dicts = []
    for row in rows[1:]:
        while len(row) < len(header):
            row.append("")
        room_dicts.append(dict(zip(header, row)))

    return room_dicts

