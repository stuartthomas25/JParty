#!/bin/sh
rm -R build
rm -R dist
pyinstaller -y JParty.spec
cd dist
zip -r JParty.zip JParty.app/
scp JParty.zip millie:/var/www/html/
cd -
