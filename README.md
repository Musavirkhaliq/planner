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

run the server
```bash
 python -m uvicorn app.main:app --reload --port 9000
```