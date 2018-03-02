#!/usr/bin/env bash
apt-get update
apt-get install -y python3-dev
apt-get install -y python3-pip
pip3 install --upgrade pip
pip3 install  matplotlib
pip3 install jupyter
pip3 install pandas==0.19.2
pip3 install pandas-datareader

tar xvzf /vagrant/ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
pip3 install TA-Lib

# python3 -m pip install pygame --user
# pip3 install tensorflow