#!/bin/sh
rm -R build
rm -R dist
pyinstaller cli.py --name JParty --onefile -w -i resources/icon.icns
