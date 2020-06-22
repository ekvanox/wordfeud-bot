# Wordfeud addon for T-800
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version](https://img.shields.io/github/v/release/Pricehacker/wordfeud-bot)](https://img.shields.io/github/v/release/Pricehacker/wordfeud-bot)

A python script that impersonates T-800 while automatically laying out moves using the private wordfeud API.

## Installation

To clone and run this repository you'll need Git and python3 (which includes pip) installed on your computer. From your command line:

```bash
# Clone this repository
git clone https://github.com/Pricehacker/wordfeud-bot
# Go into the repository
cd wordfeud-bot
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Windows

Set your wordfeud account credentials as enviroment variables (you only have to do this once):

```cmd
:: Set the username
setx WORDFEUD_USERNAME {your user ID here}
:: Set the password
setx WORDFEUD_PASSWORD {your password here}
```

Start the script normally:

```cmd
:: Go into the repository
cd wordfeud-bot
:: Execute with python
python3 main.py
```

### Linux

Set your wordfeud account credentials as enviroment variables:

```Bash
# Set the username
WORDFEUD_USERNAME={your user ID here}
# Set the password
WORDFEUD_PASSWORD={your password here}
```
Note: To add them permanently you have to edit your ```~/.bashrc``` or ```~/.profile``` file and add them there.

Start the script normally:

```bash
:: Go into the repository
cd wordfeud-bot
:: Execute with python
python3 main.py
```

## Compatibility

#### Operating systems (tested)

- Windows 10 10.0.19592 Build 19592
- Kali GNU/Linux 2020.2
- Ubuntu 18.04.4 LTS

#### Python versions (tested)

- 3.8.2
- 3.6.10
