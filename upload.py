import pickle, os, io, base64
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']

def get_gdrive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            flow.redirect_uri = 'http://localhost:8000'
            creds = flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_video(service, file):
    file_metadata = {'name': 'name'}
    media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype='video/mp4', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
    return file.get('id')

def delete_video(service, id):
    service.files().delete(fileId=id).execute()
    service.files().emptyTrash().execute()

def pictures(file):
    pic = base64.b64encode(file.read()).decode("utf-8")
    by = io.BytesIO()
    img = Image.open(file.stream)
    img.save(by, quality=10, format='JPEG', optimize=True)
    pic_low = base64.b64encode(by.getvalue()).decode('utf-8')
    return pic, pic_low
