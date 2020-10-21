# CPme
Just a simple tool to analyze your Check Point environment,
for R80.20 and above.

## Installation (Automatic)
```curl_cli https://raw.githubusercontent.com/0x7c2/cpme/main/cpme-install.sh -k | bash```

## Installation (Manual)
```
curl_cli https://codeload.github.com/0x7c2/cpme/tar.gz/main -k -o cpme-py.tgz
tar xzvf cpme-py.tgz
sed -i "1s|.*|#!$FWDIR/Python/bin/python3|" cpme-main/cpme.py
chmod +x cpme-main/cpme.py
./cpme-main/cpme.py
```

## Usage (interactive)
Run command from expert mode (bash):  
```cpme```

## Usage (only run HTML report)
Run command from expert mode (bash):   
```cpme --html```


## History
v0.22 - fixes for troubleshooting options and other small stuff
v0.20 - 0.21 - some fixes for r80.40, other small stuff  
v0.19 - measure kernel delay for routed traffic (EXPERIMENTAL!)  
v0.16 - 0.18 - added some improvements, ica certificate checks, and much more  
v0.15 - added some vpn checks, global properties, and much more  
v0.14 - modified html report, added some additional health checks  
v0.13 - first ability to create html report based on health checks  
v0.12 - checks for management (validations, ips, ...), clusterxl sync stat  
v0.11 - added troubleshooting for heavy connections  
v0.9 - 0.10 - management cleanup, fixes for r80.40  
v0.6 - 0.7 - added management functions  
v0.2 - 0.5 - added some functions  
v0.1 - initial release  

## Credits
- SVA System Vertrieb Alexander GmbH, https://www.sva.de/

## License and Author
- Simon Brecht, 0x7c2

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

```http://www.apache.org/licenses/LICENSE-2.0```

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Donation
If you want to support this project, you can donate me ;-)  

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=GZLQVAYV79AVQ&source=url)
