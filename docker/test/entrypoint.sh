#!/bin/bash
set -e

echo "🔧 AutoTrade Test Container Starting..."

# Update config.json with environment variables for testing
if [ -n "$DB_HOST" ]; then
    echo "🔧 Updating database host to: $DB_HOST"
    sed -i "s/\"host\": \"localhost\"/\"host\": \"$DB_HOST\"/" /app/src/config/config.json
fi

if [ -n "$DB_PORT" ]; then
    echo "🔧 Updating database port to: $DB_PORT"
    sed -i "s/\"port\": 5434/\"port\": $DB_PORT/" /app/src/config/config.json
fi

if [ -n "$DB_USER" ]; then
    echo "🔧 Updating database user to: $DB_USER"
    sed -i "s/\"user\": \".*\"/\"user\": \"$DB_USER\"/" /app/src/config/config.json
fi

if [ -n "$DB_PASSWORD" ]; then
    echo "🔧 Updating database password"
    sed -i "s/\"password\": \".*\"/\"password\": \"$DB_PASSWORD\"/" /app/src/config/config.json
fi

if [ -n "$DB_NAME" ]; then
    echo "🔧 Updating database name to: $DB_NAME"
    sed -i "s/\"database\": \".*\"/\"database\": \"$DB_NAME\"/" /app/src/config/config.json
fi

# Wait for PostgreSQL to be ready
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    echo "🔧 Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
        echo "⏳ PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "✅ PostgreSQL is ready!"
fi

echo "🚀 Container ready - executing command: $@"

# Execute the command passed to the container
exec "$@"