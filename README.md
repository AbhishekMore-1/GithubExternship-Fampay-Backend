# GithubExternship-Fampay-Backend
To make an API to fetch latest videos sorted in reverse chronological order of their publishing date-time from YouTube for a given tag/search query in a paginated response.

### Instruction for running the project
- Install Python 3.10
- Install pipenv

    pip install pipenv
- Create .venv folder to localize the python virtual environment
- Run following command to create python virtual environment

    pipenv shell
- Then install project dependacies by following command

    pipenv install
- Then exit from pipenv shell using following command

    exit
- Then migrate the django models using following command

    python manage.py migrate
- And fire up the server

    python manage.py runserver