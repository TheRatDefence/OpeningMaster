# OpeningMaster

---

## User Docs
https://sites.google.com/education.nsw.gov.au/openingmaster/

## Installation

#### Dependencies
After downloading the codebase, install the required python packages from requirements.txt using the command:
```
pip install -r .\requirements.txt
```

#### Database Encryption
Once all packages have been installed, open the ```.env.example``` file.
This file contains two variables:
```
APP_SECRET="your-secret-key-here"
SALT="your-salt-value-here"
```
Replace the strings with your values, then save the file as ```.env``` (without ```.example```).

# Usage
To use the app, simply run ```main.py``` via python after completing the installation steps.

Additionally, there is a list of config options that are accessible in ```config.py```.