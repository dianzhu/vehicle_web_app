# Local Setup

***
1. Set up MySQL with username and paswword, then create database called cs6400_app in MySQL
2. Create and activate venv
3. Create `.env` file and enter variables:
   DB_HOST=localhost
   DB_NAME=cs6400_app
   DB_USER=cs6400_db
   DB_PASS=vA19qv1Q*u[b
4. Install dependencies `pip install -r req.txt`
5. Run db init `flask --app app init-db`
6. Run flask app `flask --app app run`
7. The app will be running on http://127.0.0.1:5000

***
## Notes
***
`schema.sql` has all the creation tables sql. We add scripts there to add in data for static tables.

Main pages and routes will live in pages.py, auth related routes and logic will live in auth.py.

App config is in __init__.py and database connection related stuff lives in db.py.