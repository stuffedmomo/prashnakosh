#!/bin/bash

# Prashnakosh Deployment Script
# This script automates the deployment of Prashnakosh to a Ubuntu server

set -e  # Exit on error

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi

# Welcome message
echo "====================================================================="
echo "               Prashnakosh Deployment Script                         "
echo "====================================================================="
echo "This script will set up Prashnakosh on your server."
echo "Make sure you have the necessary environment variables ready."
echo ""

# Variables
APP_USER="prashnakosh"
APP_DIR="/home/$APP_USER/app"
DOMAIN="prashnakosh.in"
WWW_DOMAIN="www.prashnakosh.in"
STATIC_DIR="$APP_DIR/staticfiles"
MEDIA_DIR="$APP_DIR/mediafiles"
LOG_DIR="/var/log/prashnakosh"

# Ask for confirmation
read -p "Continue with setup? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# System updates
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx \
    postgresql-client ufw git supervisor

# Set up firewall
echo "Setting up firewall..."
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
ufw --force enable

# Create application user
echo "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

# Create directories
echo "Creating necessary directories..."
mkdir -p $APP_DIR
mkdir -p $STATIC_DIR
mkdir -p $MEDIA_DIR
mkdir -p $LOG_DIR

# Set permissions
echo "Setting directory permissions..."
chown -R $APP_USER:www-data $APP_DIR
chown -R $APP_USER:www-data $LOG_DIR
chmod -R 755 $APP_DIR

# Clone the repository (as the app user)
echo "Cloning repository..."
sudo -u $APP_USER bash << EOF
cd $APP_DIR
git clone https://github.com/stuffedmomo/prashnakosh.git .
EOF

# Set up virtual environment
echo "Setting up virtual environment..."
sudo -u $APP_USER bash << EOF
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# Prompt for environment variables
echo "Setting up environment variables..."
read -p "Django Secret Key: " DJANGO_SECRET_KEY
read -p "Supabase DB Name: " DB_NAME
read -p "Supabase DB User: " DB_USER
read -sp "Supabase DB Password: " DB_PASSWORD
echo ""
read -p "Supabase DB Host: " DB_HOST
read -p "Supabase DB Port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}
read -p "Google Analytics ID (optional): " GOOGLE_ANALYTICS_ID
read -p "Sentry DSN (optional): " SENTRY_DSN
read -p "Admin Email: " ADMIN_EMAIL

# Create .env file
echo "Creating .env file..."
sudo -u $APP_USER bash << EOF
cat > $APP_DIR/.env << EOL
DJANGO_ENV=production
DJANGO_SECRET_KEY='$DJANGO_SECRET_KEY'
DJANGO_SETTINGS_MODULE=prashnakosh.settings_production

# Database
DB_NAME='$DB_NAME'
DB_USER='$DB_USER'
DB_PASSWORD='$DB_PASSWORD'
DB_HOST='$DB_HOST'
DB_PORT='$DB_PORT'

# Analytics and Monitoring
GOOGLE_ANALYTICS_ID='$GOOGLE_ANALYTICS_ID'
SENTRY_DSN='$SENTRY_DSN'

# Admin
ADMIN_EMAIL='$ADMIN_EMAIL'

# Debug should be False in production
DEBUG=False
EOL
EOF

# Set up database migrations and static files
echo "Running migrations and collecting static files..."
sudo -u $APP_USER bash << EOF
cd $APP_DIR
source venv/bin/activate
python manage.py migrate --settings=prashnakosh.settings_production
python manage.py collectstatic --settings=prashnakosh.settings_production --no-input
EOF

# Set up Gunicorn service
echo "Setting up Gunicorn service..."
cat > /etc/systemd/system/prashnakosh.service << EOF
[Unit]
Description=Prashnakosh gunicorn daemon
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --access-logfile - \\
    --workers 3 \\
    --bind unix:$APP_DIR/prashnakosh.sock \\
    prashnakosh.wsgi_production:application
Restart=on-failure
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx
echo "Setting up Nginx configuration..."
cat > /etc/nginx/sites-available/prashnakosh << EOF
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;

    access_log /var/log/nginx/prashnakosh_access.log;
    error_log /var/log/nginx/prashnakosh_error.log;

    # Static files
    location /static/ {
        alias $STATIC_DIR/;
    }

    # Media files
    location /media/ {
        alias $MEDIA_DIR/;
    }

    # Proxy connections to the application server
    location / {
        proxy_pass http://unix:$APP_DIR/prashnakosh.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the Nginx site
ln -sf /etc/nginx/sites-available/prashnakosh /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test Nginx config
nginx -t

# Set up SSL
echo "Setting up SSL with Let's Encrypt..."
certbot --nginx -d $DOMAIN -d $WWW_DOMAIN

# Set up log rotation
echo "Setting up log rotation..."
cat > /etc/logrotate.d/prashnakosh << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 $APP_USER www-data
    sharedscripts
    postrotate
        systemctl reload prashnakosh.service
    endscript
}
EOF

# Start and enable services
echo "Starting services..."
systemctl daemon-reload
systemctl start prashnakosh
systemctl enable prashnakosh
systemctl restart nginx

# Setup complete
echo "====================================================================="
echo "                    Prashnakosh Setup Complete!                      "
echo "====================================================================="
echo "Your application should now be running at https://$DOMAIN"
echo ""
echo "To check the status, run: systemctl status prashnakosh"
echo "To view logs, run: journalctl -u prashnakosh"
echo ""
echo "Don't forget to set up regular backups for your database!"
echo "=====================================================================" 