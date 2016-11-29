RSS-Bot für Telegram
=====================

1. `git clone https://gitlab.com/iCON/rssbot`
2. `sudo apt-get install python3 python3-pip`
3. `sudo pip3 install -r requirements.txt`
4. `cp config.ini.example config.ini`
5. Bot-Token in `config.ini` einfügen
   1. Weitere Einstellungen für Redis vornehmen, falls vom Standard abweicht
6. `bot.py` öffnen und unter `def can_use(update):` die ID zur eigenen abändern
7. `python3 bot.py`

(c) 2016 Andreas Bielawski