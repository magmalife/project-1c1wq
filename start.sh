#!/bin/bash
source .venv/bin/activate
export HEVY_API_KEY=dummy
export HEVY_API_KEY_URL=http://localhost:8123/api/hevyless/v1
hevy2garmin serve
