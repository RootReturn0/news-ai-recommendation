source .env

echo "Setting Telegram bot webhook..."

curl --location "https://api.telegram.org/bot8741149070:AAE_a47gysYg-R7L4HwrmxwEbJNKVoa1JuE/setWebhook" \
--header 'Content-Type: application/json' \
--data '{
	"url": "https://curblike-hypereutectoid-iona.ngrok-free.dev/telegram/webhook",
    "allowed_updates": ["message", "message_reaction", "message_reaction_count"],
    "drop_pending_updates": true
}'