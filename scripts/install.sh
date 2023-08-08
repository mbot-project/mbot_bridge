#!/bin/bash
set -e  # Quit on error.

# Python installation.
echo "Installing the Python MBot Bridge code..."
echo
sudo pip install .

# Websockets C++ dependency installation.
echo
echo "Installing dependencies for the API..."
echo
wget https://github.com/zaphoyd/websocketpp/archive/refs/tags/0.8.2.tar.gz
tar -xzf 0.8.2.tar.gz
cd websocketpp-0.8.2/
mkdir build && cd build
cmake ..
make
sudo make install

echo
echo "Cleaning up..."
echo
cd ../../
rm 0.8.2.tar.gz
rm -rf websocketpp-0.8.2/

# C++ API installation.
echo
echo "Building the C++ MBot API..."
echo
python setup.py build_ext

echo
echo "Installing the C++ MBot API..."
echo
sudo python setup.py install_ext
