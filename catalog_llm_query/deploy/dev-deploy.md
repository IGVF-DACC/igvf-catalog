# Deploy

## Install Dependencies

Download the repo in a folder called "flask" and install all dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv -y
```

In the app folder:

```bash
python3 -m venv flaskvenv
source flaskvenv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## Gunicorn Configuration

1. Configure development.json with the correct ArangoDB database credentials and LLM settings.

2. Test Gunicorn locally:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

you can test the Flask app using a tool like curl:

```bash
curl  http://127.0.0.1:5000/query?query=Tell%20me%20about%20the%20gene%20SAMD11
```

3. Start the Flask app with pm2 to run in the background:

```bash
pm2 start "gunicorn --workers 4 -t 200 --bind 0.0.0.0:5000 app:app" --name llm
```
