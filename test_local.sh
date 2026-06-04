source .venv/bin/activate
export HEVY_API_KEY=dummy
export HEVY_API_KEY_URL=http://localhost:8123/api/hevyless/v1

hevy2garmin serve &
APP_PID=$!
sleep 2

curl -s http://localhost:8123/ > /dev/null
echo "Dashboard loaded"

kill $APP_PID
