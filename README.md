# Infirmary Emergency Desk (Vercel version)

Flask + Postgres (Neon) + a hand-written max-heap priority queue (pq.py).

Files
  app.py            Flask backend (all /api routes)
  pq.py             Binary max-heap priority queue
  public/index.html Frontend (served by Vercel's CDN)
  requirements.txt  Flask, psycopg2-binary

Environment variables (Vercel > Project > Settings > Environment Variables)
  SECRET_KEY        long random text (signs login cookies)
  STAFF_CODE        code staff must enter to register
  INFIRMARY_PHONE   infirmary phone number shown in the Call box
  DATABASE_URL      added automatically when you connect Neon storage

Run on your laptop (no database setup needed - uses a local SQLite file):
  pip install -r requirements.txt
  python app.py        -> http://127.0.0.1:5000
