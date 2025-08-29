#!/usr/bin/python3
#
# author: Wilko Quak (w.quak@geonovum.nl)
#
# Dit script checkt alle Geonovum repositories uit en houdt ze up to date.
# Vereisten:
# - Github client is geinstalleerd: (sudo apt-get install gh)
# - Authenticatie regel (export GH_TOKEN=)
#
import subprocess
import json
import os
from git import Repo

output = subprocess.check_output('gh repo list Geonovum -L 400 --json name,isEmpty',shell=True)
data = json.loads(output)

#
# For small tests you can run the script with only this repo.
#
#data = json.loads('''
#[
#  {
#    #"name": "dso-cimop"
#  },
#  {
#    "name": "DashboardGit"
#  }
#]
#''')

for x in data:
    repo = x['name']
    isEmpty = x['isEmpty']
    
    if isEmpty:
        print('skipping repo {} because empty.'.format(repo))
    elif os.path.isdir(repo):
        print('repo {} exists updating'.format(repo))
        subprocess.check_output('cd {}; gh repo sync --force'.format(repo),shell=True)
    else:
        print('repo {} does not exist checking out'.format(repo))
        print('gh repo clone Geonovum/{}'.format(repo))
        subprocess.check_output('gh repo clone Geonovum/{}'.format(repo),shell=True)
