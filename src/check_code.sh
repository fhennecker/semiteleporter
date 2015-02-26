#!/bin/bash

sources="mesher/*.py gui/*.py scanner/*.py"

echo "--------------------- PEP8 ---------------------"
pep8 --ignore=E501 $sources

echo "-------------------- Flakes --------------------"
pyflakes $sources