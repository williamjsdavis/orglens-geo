# Backend Notes

## Running the backend

To set up:

1. Set up the virtual environment as described in the main `README.md` file.
2. Run `python fetch.py` to fetch the data from the GitHub API. 
3. Run `python manage.py populate <input.json> --clear` to populate the database.
4. Run `python manage.py create_summaries` to create the summaries for the database.
5. Run `python manage.py runserver` to run the server.
