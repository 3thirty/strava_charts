### General:
  * [ ] write a readme
  * [ ] cleanup comments
  * [ ] loading state

### Strava:
  * [x] use a real callback
  * [x] cache data
  * [x] cache oauth credentials for multiple users properly; in a cookie?
  * [x] recursively fetch pages Strava.py
  * [x] move config to yaml (do not commit secrets!)
  * [x] read secrets from env vars
  * [ ] choose any metric
  * [x] allow user to force bypass cache 
  * [ ] aggregate by week/month/whatever?
  * [x] cleanup cookie token storage
  * [x] reduce cache time
  * [ ] add update option to skip cache for current page only
  * [ ] don't use a hardcoded number of activities - keep going back till we get everything?

### server
  * [ ] clean up handling/parsing of activities

### Charts:
  * [x] use complete time range for x axis
  * [x] order data correctly
  * [ ] start new series if more than X days are missed
  * [ ] moving average
  * [ ] trend line
  * [ ] add UI for selecting aggregate time period and metric
  * [ ] add option for charting against goal (distance/time/elevation)
  * weekly aggregrates
    * [x] sort
    * [x] use week start date instead of week number
    * [ ] update week data to use complete time range
