# Local Setup

***
1. Set up MySQL with username and paswword, then create database called cs6400_app in MySQL
2. Create and activate venv
3. Create `.env` file and enter variables:
   
   DB_HOST=localhost
   
   DB_NAME=cs6400_app
   
   DB_USER=your mysql username
   
   DB_PASS=your mysql password
   
5. Install dependencies `pip install -r req.txt`
6. Run db init `flask --app app init-db`
7. Run flask app `flask --app app run`
8. The app will be running on http://127.0.0.1:5000

***
## Notes
***
`schema.sql` has all the creation tables sql. We add scripts there to add in data for static tables.

Main pages and routes will live in pages.py, auth related routes and logic will live in auth.py.

App config is in __init__.py and database connection related stuff lives in db.py.
