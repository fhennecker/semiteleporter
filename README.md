# Semi-teleporter

A low-cost 3D scanner for a university project. 
It may digitalize you and your thoughts inside a computer, but it cannot send you
to another galaxy over the air.

## Requirements

Package name for Debian (Ubuntu, Mint, ...) in brackets

* Python 2.7 
* numpy 
* opencv
* matplotlib with support for TkAgg
* TKinter with support for images from PIL

### Install

    sudo apt-get update
    sudo apt-get install tk-dev libpng-dev libffi-dev dvipng texlive-latex-base python-tk python-dev python-imaging-tk python-pip python-vtk
    sudo pip install numpy matplotlib pyopencv
    ./install-ballpivoting.sh

### Run

    cd src/
    python scan.py
