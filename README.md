# Stethoscope / Heartbeat alerter

Simple code to send alerts if a heartbeat is not received.

The behaviour is hard-coded, to keep the code simple (no config validation needed).

![Logo](logo.png)


## Installation / usage

* Install this repo contents in `/opt/stsc` or another location.
* Install dependencies: `pip install -r requirements.txt`.
* Create a config file and edit it to set your credentials: `cp config-example.ini config.ini`. Caution: `.gitignore` doesn't seem to work - take care not to commit sensitive data.

Optional:

* Create a systemd unit. `cp stethoscope.service /etc/systemd/system`. Edit the username and paths if required.
* `systemctl daemon-reload`; `systemctl enable stethoscope.service`; 
    `systemctl start stethoscope.service`

## Protocol

The system to monitor should send a POST request to http://<hostname>:64250/heartbeat every minute
(<hostname> being the host on which this flask app is running).

It can send a request to http://<hostname>:64250/explicit_alarm to trigger a generic alarm message (useful as a fallback alarm mechanism).
