### General:
  * [x] write a readme
  * [ ] cleanup comments
  * [ ] loading state
  * [x] docker build: cache pip packages so we don't have to download every time
  * Update GHA workflow to use cached docker layers
  * [x] investigate GHA or CDK or something to publish to AWS lambda
  * Better handling of dev/prod config

### Strava:
  * [ ] fetch older data asynchronously
  * [ ] allow filtering of activity types
  * [x] switch caching to redis (or other distributed store). without it, we can't have concurrency

### server
  * [ ] clean up handling/parsing of activities

### Charts:
  * [ ] trend line
  * [x] add UI for selecting aggregate time period and metric
  * [ ] add option for charting against goal (distance/time/elevation)
  * [ ] formatting rules for metrics (e.g. distance should be ÷ 100 and shown with `km` units, speed should be kmph or similar, currently meters per second)
