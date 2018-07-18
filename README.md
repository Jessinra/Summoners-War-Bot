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
```
Open your account on your mobile device.
Tap on your Account info in the top left corner.
Press Com2Us-Hive.
Open the menu on the top left.
Scroll to the bottom to find you DID.
Go to config.json and replace null with "your DID"
```

Set up your account:
```
Open mybot.py with any text editor.
Scroll to the bottom to "if __name__ == "__main__":".
Set "user = ''" to "user = 'your hive id'".
Set "user_mail = ''" to "user = 'your hive e-mail'".
Set "pw = ''" to "pw = 'your hive password'".
Set "region = ''" to "region = 'your region'". (gb = global, eu = europe, jp = japan, sea = asia, cn = china)
```

### Run the bot
```
$ pipenv run python mybot.py
```