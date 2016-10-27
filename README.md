# Downtime Monitor
Add URLs to yaml file. On error will send message to slack channel

Supports custom interval, trigger frequency, and time windows (in case you don't want to monitor during specific times of day)

# Usage

Configure `config.yaml` file
```
interval: 5 # how often to poll
trigger_frequency: 15 # how often to send message to slack channel
triggers:
  random_slack_channel:
      type: "slack" # currently only type supported
      channel: "#random"
      url: "<url>" # url given from slack webhooks
  engineering_channel:
      type: "slack"
      channel: "#engineering"
      url: "<url>"
monitors:
  mysite:
      name: "My Website"
      url: "http://mywebsite.com"
      interval: 30 # overrides default interval
      on_error: # will send to both channels
        - engineering_channel
        - random_channel
  myothersite:
      name: "Google"
      url: "http://google.com"
      ignore_hours: [3,4,5,6,7,8] # ignore 3AM-8AM
      on_error:
        - engineering_channel
```
# Install it
`pip install -r requirements.txt`

Or use docker container attached

# Run it
`python run.py`
or with docker container
`docker-compose up -d`
