# Planner


## Local Development Setup
clone the repository
```bash
git clone https://github.com/Musavirkhaliq/planner.git
```
change directory
```bash
cd planner
```

create a virtual environment
```bash
python -m venv venv
```

activate the virtual environment
```bash
source venv/bin/activate
```

install dependencies
```bash
pip install -r requirements.txt
```

create a .env file and add the following variables
```bash
cp .env.example .env

Create app.db file
```bash
touch app.db
```

GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"

# if you put these here to please update config.py
DATABASE_URL="your_database_url"
SECRET_KEY="your_secret_key"
ALGORITHM="your_algorithm"
ACCESS_TOKEN_EXPIRE_MINUTES="your_access_token_expire_minutes"
```

run the server
```bash
 python -m uvicorn app.main:app --reload --port 9000
```

view app here
http://localhost:9000/

view swagger api docs here
http://localhost:9000/docs

view redoc api docs here
http://localhost:9000/redoc