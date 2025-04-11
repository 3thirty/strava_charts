.PHONY: install run creds clean open zip docker-build docker-run docker-kill

install:
	pip3 install requests-oauthlib bottle requests-cache pyyaml gunicorn bottle-beaker pychart.js

dev: creds
	test -e cert.crt && test -e private.key || openssl req -new -x509 -days 1095 -nodes -newkey rsa:2048 -out cert.crt -keyout private.key -subj '/CN=localhost'

	env OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python3 application.py dev

creds:
	echo "Checking for STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET"
	test -n "$(STRAVA_CLIENT_ID)"
	test -n "$(STRAVA_CLIENT_SECRET)"

clean:
	-rm -rf __pycache__
	-rm cache.sqlite
	-rm -rf build

open:
	open "https://localhost:8080/chart"

zip: clean
	-mkdir build
	zip -r build/strava_charts.zip ./* --exclude @.gitignore

docker-build:
	docker build . -t strava_charts

docker-build-dev:
	docker build -f Dockerfile.dev . -t strava_charts

docker-run: docker-kill
	docker run --rm --name strava_charts --env-file .env -p 8080:8080 strava_charts

docker-kill:
	-docker kill strava_charts
	-docker rm strava_charts
	sleep 1
