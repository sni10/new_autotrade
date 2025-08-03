#!/bin/bash

# Update config.json with environment variables for testing
if [ -n "$DB_HOST" ]; then
    sed -i "s/\"host\": \"localhost\"/\"host\": \"$DB_HOST\"/" /app/src/config/config.json
fi
if [ -n "$DB_PORT" ]; then
    sed -i "s/\"port\": 5434/\"port\": $DB_PORT/" /app/src/config/config.json
fi

# Wait for PostgreSQL to be ready
echo "🔧 Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
    echo "⏳ PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Execute the command passed to the container
exec "$@"