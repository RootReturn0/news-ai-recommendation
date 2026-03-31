source .env

echo "Setting Telegram bot webhook..."

curl --location "https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook" \
--header 'Content-Type: application/json' \
--data '{
	"url": "'$TG_BASE_URL/telegram/webhook'",
    "allowed_updates": ["message", "message_reaction", "message_reaction_count"],
    "drop_pending_updates": true
}'