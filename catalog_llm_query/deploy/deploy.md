# Deploy

## Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx -y
```

In the app folder:

```bash
python3 -m venv flaskvenv
source flaskvenv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## Gunicorn Configuration

1. Test Gunicorn locally

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

If you can access <http://your-ec2-instance-ip:5000> in your browser, it's working.

1. Set up a systemd service for Gunicorn. The example file is in the deploy folder.

```bash
sudo cp /home/ubuntu/flask/catalog_llm_query/deploy/llm.service /etc/systemd/system/llm.service
```

## Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl start llm
sudo systemctl enable llm
sudo systemctl status llm
```

## Set Up Nginx as Reverse Proxy

Create an Nginx configuration file

```bash
sudo cp /home/ubuntu/flask/catalog_llm_query/deploy/nginx /etc/nginx/sites-available/default
```

## Enable Nginx

```bash
sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Allow HTTP Traffic

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```
