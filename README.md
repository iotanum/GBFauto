# GBFauto

Work in progress "Granblue Fantasy" bot that can do various tasks.

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
