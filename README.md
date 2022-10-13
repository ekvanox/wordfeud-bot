# Wordfeud addon for T-800

[![Version](https://img.shields.io/github/v/release/ekvanox/wordfeud-bot)](https://img.shields.io/github/v/release/ekvanox/wordfeud-bot)
![GitHub repo size](https://img.shields.io/github/repo-size/ekvanox/wordfeud-bot)
[![CodeFactor](https://www.codefactor.io/repository/github/ekvanox/wordfeud-bot/badge)](https://www.codefactor.io/repository/github/ekvanox/wordfeud-bot)
[![Build Status](https://travis-ci.com/ekvanox/wordfeud-bot.svg?branch=master)](https://travis-ci.com/ekvanox/wordfeud-bot)
![License](https://img.shields.io/github/license/ekvanox/wordfeud-bot)

A python script that impersonates T-800 while automatically laying out moves using the private wordfeud API.

## Installation

To clone and run this repository you'll need Git and python3 (which includes pip3) installed on your computer. From your command line:

```bash
# Clone this repository
git clone https://github.com/ekvanox/wordfeud-bot
# Go into the repository
cd wordfeud-bot
# Install dependencies
pip install -r requirements.txt
```

## Collecting credentials

Currently, the credentials (user ID & password) are not captured by the wordfeud bot itself, and therefore have to be found prior to using it.

[Here](https://heimdal.dev/projects/wordfeud-bot/) is a guide on how to do so (windows only)

## Usage

### Windows

Set your wordfeud account credentials as environment variables (you only have to do this once):

```cmd
:: Set the username (remove the curly braces)
setx WORDFEUD_USERNAME {your user ID here}
:: Set the password (remove the curly braces)
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

Set your wordfeud account credentials as environment variables:

```Bash
# Set the username (remove the curly braces)
WORDFEUD_USERNAME={your user ID here}
# Set the password (remove the curly braces)
WORDFEUD_PASSWORD={your password here}
```

Note: To add them permanently you have to edit your `~/.bashrc` or `~/.profile` file and add them there.

Start the script normally:

```bash
# Go into the repository
cd wordfeud-bot
# Execute with python
python3 main.py
```

### Docker

Build your docker image:

```bash
# Go into the repository
cd wordfeud-bot
# Build the docker image
docker build -t wordfeudbot .
```

Start docker container with your credentials as environment variables:

```bash
# Remove the curly braces
docker run -e WORDFEUD_USERNAME={your user ID here} -e WORDFEUD_PASSWORD={your password here} wordfeudbot
```

### Python package installer

Download and install the package:

```bash
# Install the package with pip
pip install wordfeudbot
```

Run the script with credentials as arguments:

```bash
# Remove the curly braces
wordfeudbot --user_id {your user ID here} --password {your password here}
```

Note: Credentials are optional if you set environment variables.

## Compatibility

### Operating systems (tested)

- Windows 10 10.0.19592 Build 19592
- Kali GNU/Linux 2020.2
- Ubuntu 18.04.4 LTS

### Python versions (tested)

- 3.8.2
- 3.6.10

## Read more

Documentation from the development process can be found [here](https://heimdal.dev/projects/wordfeud-bot/).
