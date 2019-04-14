#!/usr/bin/env bash
apt-get update
apt-get install -y python3-dev
apt-get install -y python3-pip
pip3 install --upgrade pip
pip3 install  matplotlib==2.1.2
pip3 install jupyter
pip3 install pandas==0.19.2
pip3 install beautifulsoup4==4.6.0
pip3 install plotly
pip3 install stockstats

tar xvzf /vagrant/ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
pip3 install TA-Lib

# python3 -m pip install pygame --user
# pip3 install tensorflow