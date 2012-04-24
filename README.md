StatusBoard
=

StatusBoard is a Tornado application we use to display a Web page with info about things that are going on around our office.

Channels and workers
-

The app uses SSE (wrapped with [BTHEventSource](https://github.com/tomekwojcik/BTHEventSource)) to communicate with browsers.

The config.py.default file defines a single channel for Pinger. `channel_name` will be used as an SSE event name.

Workers provide data for channels. There are two types of workers:

1. `StatusBoard.worker.PeriodicWorker` - invoked periodically at a given interval,
1. `StatusBoard.worker.ScheduledWorker` - one-shot worker invoked after scheduling.

There are four workers in the box:

1. `StatusBoard.workers.PingerWorker` - pings computers defined in config to determine number of present and absent people,
1. `StatusBoard.workers.RedmineWorker` - connects the app to Redmine instance to provide info about projects status,
1. `StatusBoard.workers.YahooWeatherWorker` - fetches weather info from Yahoo! Weather,
1. `StatusBoard.workers.XMPPBot` - controls XMPP bot that feeds _Breaking News_ section.

The config.py file
-
config.py contains a dictionary that'll be loaded by `status_board` and passed to Tornado app. It's the place to provide app's config. For more info about default fields see Tornado.

App-specific config dict fields:

+ `xmpp_bot` - XMPP bot config. _database_ field should contain **absolute** path to a SQLite file created by `status_board_setup_db` or `None` if you wish to ignore the DB.
+ `people` - list of dicts containing people definition. Mandatory fields are `name` and `gravatar_mail`. `ip` is used by PingerWorker. `jid` is used by XMPPBot, `redmine_mail` by RedmineWorker and workers will fall back to `gravatar_mail` automagically if their fields aren't present.
+ `redmine.issue_trackers` - contains a dict of issue trackers. The syntax is `<id>: "<name>"`. Consult Redmine API for more info.
+ The rest is pretty self-explanatory so it's pointless to document it :).

The file also contains a dict of channel definitions. The syntax is `'<channel_name>': WorkerClass`. The `status_board` script will set up workers for the channels.

Logos
-
If you wish to add your logos to the app place files `logo.png` and `blanker_logo.png` in `app_config['logo_path']`. config.py sets `logo_path` to the directory where the file is located. Feel free to change the path.

Use a 187px x 119px image for `logo.png`. `blanker_logo.png` will be centered in the viewport automatically.

Credits
-
Weather state icons: http://vclouds.deviantart.com/art/VClouds-Weather-Icons-179152045 (CC BY-NC-SA 3.0)

Installation, setup and running
-
1. Create a virtualenv, activate it, clone the repo and cd to it,
1. `python setup.py install` (requires distribute)
1. `cp config.py.default config.py`
1. `status_board_setup_db` (optional)
1. `vim config.py`
1. `status_board`
1. Point the browser to app's URL (see `status_board --help` for info).
1. Sit down and watch the magic happen.
1. Profit?

License
-
BSD License