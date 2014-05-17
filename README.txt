DibLib Printers Library Project

Displays collective printer information.
status.researcher.poly.edu:3000

cronjobs:

(crontab -e)
* * * * * /home/peter/pyEnv/bin/python /home/peter/printersOfGlory.py
* * * * * ( sleep 30 ; /home/peter/pyEnv/bin/python /home/peter/printersOfGlory.py )
* * * * * echo "" > /var/spool/mail/peter
* * * * * echo "" > /home/peter/printerStatus/nohup.out
0 0 * * 0 mongodump