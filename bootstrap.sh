#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install -y python3-dev
sudo apt-get install -y python3-pip
sudo pip3 install --upgrade pip
sudo pip3 install jupyter
sudo apt-get install -y python3-pandas
sudo pip install pandas-datareader

tar xvzf /vagrant/ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo pip3 install TA-Lib

# python3 -m pip install pygame --user
# pip3 install tensorflow