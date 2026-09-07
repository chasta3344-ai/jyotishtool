# Hindi Panchang Backend

Flask backend using Swiss Ephemeris, PyEphem and IST calculations.

## Render

Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn main:app --bind 0.0.0.0:$PORT`

The application reads Render's `PORT` environment variable and also supports local execution with port 5000.
