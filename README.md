# GBFauto

Work in progress "Granblue Fantasy" bot that can do various tasks.

## Description

A bot that does the most tedious tasks on Granblue.
Every popup/event (that I'm aware of) is being handled by the bot itself while it's running.
```
Supports: 

  1. Automatic log-in.
  1. Doing raids (from finding a raid to usage of skill queue inside a raid).
  2. Doing repeatable quests (includes COOP, story quests, GW type events, etc.)
  3. Skill queues (includes multi-fight quests)
  4. Custom support summon picking.
  5. Quality of life stuff, for example: refreshing after skill queue, EP/AP use, logging of various data.
```

## Installation

Clone this git repo and create two folders:
```
utils
errors
```
##
Currently bot only supports chrome browser, so it needs 'chromedriver' server. 

Read up everything you need to know here:
[http://chromedriver.chromium.org/downloads/version-selection]

After downloading a compatible chromedriver server, put the executable in **'utils'** folder.
##
Then use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
pip install -r requirements.txt
```

## Usage

**Things to do before using the bot:**
1. Turn off in-game sounds.
2. Set game screen size to the smallest.
3. 'Skip skill description' must be turned off.

**Please read and update the configuration file according to your needs.**

[.config file](config.env.example)
