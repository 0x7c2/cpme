#!/bin/bash

#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

# check running version of check point

found=0

if [ "`fw ver | grep -c "R80.40"`" == "1" ]; then
        echo "Running R80.40, continue installing..."
        found=1
fi

if [ "`fw ver | grep -c "R80.30"`" == "1" ]; then
	echo "Running R80.30, continue installing..."
	found=1
fi

if [ "`fw ver | grep -c "R80.20"`" == "1" ]; then
	echo "Running R80.20, continue installing..."
	found=1
fi

if [ $found -lt 1 ]; then
	echo "Your environment is not supported (yet), exiting."
	exit 1
fi

# download and install
cd
# cleanup old archive
[ -f ./cpme-py.tgz ] && rm ./cpme-py.tgz
curl_cli https://codeload.github.com/0x7c2/cpme/tar.gz/main  -k -o  cpme-py.tgz
tar xzvf cpme-py.tgz
# cleanup old files
[ -d ./cpme-py ] && rm -r ./cpme-py
mv ./cpme-main ./cpme-py
where="`pwd`"
sed -i "1s|.*|#!$FWDIR/Python/bin/python3|" $where/cpme-py/cpme.py
echo "#!/bin/bash" > /sbin/cpme
echo "cd $where/cpme-py" >> /sbin/cpme
echo "$where/cpme-py/cpme.py \$@" >> /sbin/cpme
chmod +x /sbin/cpme
chmod +x $where/cpme-py/cpme.py
echo
echo "Installation complete!"
echo "Just type 'cpme' to run the tool..."
echo
