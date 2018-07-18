# Summoners-War-Bot (Python 3)

Forked from https://github.com/Mila432/Summoners-War-Bot
Credits for all technical stuff go to Mila432.
Just updated his base to Python 3 and added some storing methods of all the api data and a seperate bot-tool
which should contain all the logical stuff to keep the api as clean as possible.

## Getting Started

### Prerequisites
* [Python >= 3.6](https://www.python.org/downloads/)
* [Pipenv](https://github.com/pypa/pipenv)

### Download and Installation
```
$ git clone https://github.com/fnk93/Summoners-War-Bot.git
$ pipenv install
```

### Setting up your account

Set up your device id:
1. Open your account on your mobile device.
2. Tap on your Account info in the top left corner.
3. Press Com2Us-Hive.
4. Open the menu on the top left.
5. Scroll to the bottom to find you DID.
6. Go to config.json and replace null with "your DID"

Set up your account:

1. Open mybot.py with any text editor.
2. Scroll to the bottom to "if __name__ == "__main__":".
3. Set "user = ''" to "user = 'your hive id'".
4. Set "user_mail = ''" to "user = 'your hive e-mail'".
5. Set "pw = ''" to "pw = 'your hive password'".
6. Set "region = ''" to "region = 'your region'". (gb = global, eu = europe, jp = japan, sea = asia, cn = china)

### Run the bot
```
$ pipenv run python mybot.py
```