# readSerial

This is a Python script that reads all incoming data on the serial port on Raspberry Pi

<i>i:1,t:25.44,h:40.23,l:34.00</i> (example)

The letters indicate sensor type, and the numbers indicate sensor value. In the above example, i is node ID, t is temperature, h is relative humidity and l is light intensity. The script splits each data set by commas and makes a dictionary of the data split by colons. 

This python script should run on boot as a cron job. Open cron in terminal by typing `crontab -e` and paste the following at the end of the file: 

`@reboot /usr/bin/python /home/pi/readSerial.py &`


