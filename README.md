# strava_charts
An application that provides alternative views and aggregations of your [strava](https://www.strava.com) data.

This application will first ask to connect to your strava account and will then fetch data as needed. Your strava OAuth credentials are stored on _your machine_ as a cookie. These credentials are then used by the application to fetch your data from strava. That data may be cached in the service for a maximum of 1 day

## Installing and Running
The application is setup to be built and run within a docker container (tested using orbstack)

  * Add strava key and secret to .env
  * Run `make docker-build` to build the image (currently for dev mode only)
  * Run `make docker-run` to start the application in docker, listening on port 8080
  * Run `make open` to open your browser at the charts endpoint of the application
    * Note that this will complain about the self-signed certs

### Endpoints
#### `/chart`
Produces a chart (default is average_watts by week), but may be called in the format `/chart/<type>/<metric>/<period>`, where:

  * `type` is one of: `average` or `total`
  * `metric` is one of: `average_watts`, `weighted_average_watts`, `average_speed`, `distance`, `moving_time`, `total_elevation_gain`
  * `period` is one of: `day`, `week`, `month`, `year`

Also takes optional GET arguments:
  * `after` a date in yyyy-mm-dd format. Only activities after this date will be charted
  * `limit` only chart this many activities

Examples:

  * `/chart/total/distance/year` - total distance by year
  * `/chart/average/average_watts/week` - weekly average power
  * `/chart/average/total_elevation_gain/year` - average elevation gain per ride, each year
  * `/chart/average/distance/day?after=2025-01-01&limit=365` - distance per day in 2025

#### `/dump`
Dumps all json data for the requesting user

#### `/ping`
Just for testing
