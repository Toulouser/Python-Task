python3 -m venv venv

source venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt

uvicorn main:app --reload --host 0.0.0.0 --port 8000

