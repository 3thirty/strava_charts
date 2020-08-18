.PHONY: install run creds clean open

install:
	pip3 install requests-oauthlib bottle requests-cache pyyaml gunicorn bottle-beaker

	test -e cert.crt && test -e private.key || openssl req -new -x509 -days 1095 -nodes -newkey rsa:2048 -out cert.crt -keyout private.key

run: creds
	env OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python3 server.py

creds:
	echo "Checking for STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET"
	test -n "$(STRAVA_CLIENT_ID)"
	test -n "$(STRAVA_CLIENT_SECRET)"

clean:
	rm -rf __pycache__
	rm cache.sqlite

open:
	open "https://localhost:8080/chart"
