# Deploy

## Install Dependencies

Download the repo in folder called flask then install dependecies.

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

1. Update development.json in config folder for ArangoDB dabase setting and llm setting.

1. Test Gunicorn locally

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

you can test flask app using a tool like curl:

```bash
curl  http://127.0.0.1:5000/query?query=Tell%20me%20about%20the%20gene%20SAMD11
```

1. Start flask app with pm2

```bash
pm2 start "gunicorn --workers 3 --bind 0.0.0.0:5000 app:app" --name llm
```
