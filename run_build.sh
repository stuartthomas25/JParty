#!/bin/sh
export CC=clang
export CXX=clang++
rm -R build
rm -R dist
pyinstaller -y JParty.spec
