cd /var/www/the_master_of_law || exit 1
echo "📥 Pulling latest code..."
git pull
echo "🔨 Rebuilding backend..."
cd backend
docker compose build
docker compose up -d
echo "✅ Redeployed. Checking status..."
docker compose ps