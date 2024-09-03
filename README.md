
Go to bot folder

chmod +x botsetup.sh
sudo ./botsetup.sh

This will start installing all requirements and setup nginx as well, it may show pop up for
kernel update, just press enter


*****check ufw status*****

ufw status

if it is active then run following
ufw allow "Nginx Full"

********Creating certificates*******
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ip_address.key -out ip_address.crt -addext "subjectAltName=IP:192.168.1.9"
Note:- Change IP in command to your server's ip

********create screen**********

screen -S bot

then run python3 app.py

ctrl+shift+D

to get into screen again 

screen -rd bot


Note:- static folder app.py, passport_logic.py are all in same folder

Current issue, when uploading image from camera it needs to be cropped to the content that is
crop to the passport exact size else it won't recognize the image
