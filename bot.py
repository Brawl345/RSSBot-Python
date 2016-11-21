#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# RSS Bot
# Python 3 required

import re
import redis
import feedparser

from configparser import ConfigParser
from telegram import ChatAction, ParseMode
from telegram.ext import Updater, Job, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, NetworkError, ChatMigrated)

import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Bot Configuration
config = ConfigParser()
config.read_file(open('config.ini'))

redis_conf = config['REDIS']
redis_db = redis_conf.get('db' , 0)
redis_host = redis_conf.get('host')
redis_port = redis_conf.get('port', 6379)
redis_socket = redis_conf.get('socket_path')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
logger = logging.getLogger(__name__)

# Utils
if redis_socket:
    r = redis.Redis(unix_socket_path=redis_socket, db=int(redis_db), decode_responses=True)
else:
    r = redis.Redis(host=redis_host, port=int(redis_port), db=int(redis_db), decode_responses=True)

if not r.ping():
    print('Konnte nicht mit Redis verbinden, prüfe deine Einstellungen')
    quit()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def remove_tags(html):
    return ''.join(BeautifulSoup(html,  "html.parser").findAll(text=True))
    
def can_use(update):
    unlocked = [36623702]
    if update.message.from_user.id in unlocked:
      return True
    else:
      return False

def cleanRSS(str):
  str = str.replace('[…]', '')
  str = str.replace('[bilder]', '')
  str = str.replace('[mehr]', '')
  str = str.replace('[video]', '')
  str = str.replace('...[more]', '')
  str = str.replace('[more]', '')
  str = str.replace('[liveticker]', '')
  str = str.replace('[livestream]', '')
  str = str.replace('[multimedia]', '')
  str = str.replace('[phoenix]', '')
  str = str.replace('[swr]', '')
  str = str.replace('[ndr]', '')
  str = str.replace('[mdr]', '')
  str = str.replace('[rbb]', '')
  str = str.replace('[wdr]', '')
  str = str.replace('[hr]', '')
  str = str.replace('[br]', '')
  str = str.replace('Click for full.', '')
  str = str.replace('Read more »', '')
  str = str.replace('Read more', '')
  str = str.replace('(more…)', '')
  str = str.replace('View On WordPress', '')
  str = str.replace('(RSS generated with  FetchRss)', '')
  str = str.replace('-- Delivered by Feed43 service', '')
  str = str.replace('Meldung bei www.tagesschau.de lesen', '')
  str = str.replace('The post.*appeared first on Sugoi! Anime Blog.', '')
  str = str.replace('Der Beitrag.*erschien zuerst auf MAnime.de.', '')
  str = re.sub('http://www\.serienjunkies.de/.*\.html', '', str)
  return str
      
def check_chat(bot, username):
    try:
        return bot.getChat(username)
    except:
        return
 
# Commands
@run_async
def start(bot, update):
    if not can_use(update):
      return
    bot.sendMessage(
                    chat_id = update.message.chat_id,
                    text = '<b>Willkommen beim RSS-Bot!</b>\nLass uns anfangen! Sende /hilfe, um zu starten.',
                    reply_to_message_id = update.message.message_id,
                    parse_mode = ParseMode.HTML
                   )

@run_async
def help(bot, update):
    if not can_use(update):
      return
    bot.sendMessage(
                    chat_id = update.message.chat_id,
                    text = '<b>/rss</b>: Abonnierte Feeds anzeigen\n<b>/sub</b> <i>Feed-URL</i>: Feed abonnieren\n<b>/del</b> <i>n</i>: Feed löschen',
                    reply_to_message_id = update.message.message_id,
                    parse_mode = ParseMode.HTML
                   )

def subscribe_to_rss(bot, update, args):
    if not can_use(update):
      return
    if len(args) < 1:
      bot.sendMessage(chat_id=update.message.chat_id, text='Bitte gebe eine Feed-URL ein.', reply_to_message_id=update.message.message_id)
      return
    feed_url = args[0]
    is_url = re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", feed_url)
    if not is_url:
      bot.sendMessage(chat_id=update.message.chat_id, text='Dies ist keine URL.', reply_to_message_id=update.message.message_id)
      return

    if len(args) > 1:
      username = args[1]
      chat_info = check_chat(bot, username)
      if not chat_info:
        bot.sendMessage(chat_id=update.message.chat_id, text='Dieser Kanal existiert nicht!', reply_to_message_id=update.message.message_id)
        return
      chat_id = str(chat_info.id)
    else:
        chat_id = str(update.message.chat_id)
    
    if r.sismember('pythonbot:rss:' + chat_id, feed_url):
      bot.sendMessage(chat_id=update.message.chat_id, text='Dieser Feed wurde bereits abonniert.', reply_to_message_id=update.message.message_id)
      return

    bot.sendChatAction(update.message.chat_id, action=ChatAction.TYPING)
    feed_data = feedparser.parse(feed_url)
    if not 'link' in feed_data.feed:
      bot.sendMessage(chat_id=update.message.chat_id, text='Kein gültiger Feed.',reply_to_message_id=update.message.message_id)
      return
    
    if not 'title' in feed_data.feed:
      feed_title = 'Unbekannten Feed'
    else:
      feed_title = feed_data.feed.title
    last_entry = feed_data.entries[0].id
    lhash = 'pythonbot:rss:' + feed_url + ':last_entry'
    if not r.exists(lhash):
      r.set(lhash, last_entry)
    r.sadd('pythonbot:rss:' + feed_url + ':subs', int(chat_id))
    r.sadd('pythonbot:rss:' + chat_id, feed_url)
    bot.sendMessage(
                       chat_id = update.message.chat_id,
                       text = '<b>' + feed_title + '</b> hinzugefügt!',
                       reply_to_message_id = update.message.message_id,
                       parse_mode = ParseMode.HTML
                      )

def unsubscribe_rss(bot, update, args):
    if not can_use(update):
      return
      
    if len(args) < 1:
      bot.sendMessage(chat_id=update.message.chat_id, text='Bitte gebe eine Nummer ein', reply_to_message_id=update.message.message_id)
      return 
    
    if len(args) > 1:
      username = args[1]
      chat_info = check_chat(bot, username)
      if not chat_info:
        bot.sendMessage(chat_id=update.message.chat_id, text='Dieser Kanal existiert nicht!', reply_to_message_id=update.message.message_id)
        return
      chat_id = str(chat_info.id)
    else:
        chat_id = str(update.message.chat_id)
    
    if not is_number(args[0]):
      bot.sendMessage(chat_id=update.message.chat_id, text='Bitte gebe eine Nummer ein.', reply_to_message_id=update.message.message_id)
      return
    uhash = 'pythonbot:rss:' + chat_id
    n = int(args[0])
    subs = list(r.smembers(uhash))
    if n < 1 or n > len(subs):
        bot.sendMessage(chat_id=update.message.chat_id, text='Abonnement-ID ist zu hoch.', reply_to_message_id=update.message.message_id)
        return
    sub = subs[n-1]
    lhash = 'pythonbot:rss:' + sub + ':subs'
    r.srem(uhash, sub)
    r.srem(lhash, int(chat_id))
    bot.sendMessage(
                    chat_id = update.message.chat_id,
                    text = '<b>' + sub + '</b> entfernt.',
                    reply_to_message_id = update.message.message_id,
                    parse_mode = ParseMode.HTML
                   )
    left = r.smembers(lhash)
    if len(left) < 1: # no one subscribed, remove it
        r.delete('pythonbot:rss:' + sub + ':last_entry')

    
def get_rss_list(chat_id, chat_name):
    uhash = 'pythonbot:rss:' + chat_id
    subs = list(r.smembers(uhash))
    if len(subs) < 1:
      return '<b>Keine Feeds abonniert!</b>'
    text = '<b>' + chat_name + '</b> hat abonniert:\n'
    for n, feed in enumerate(subs):
      text = text + str(n+1) + ') ' + feed + '\n'
    return text

@run_async    
def list_rss(bot, update, args):
    if len(args) == 1:
      username = args[0]
      chat_info = check_chat(bot, username)
      if not chat_info:
        bot.sendMessage(chat_id=update.message.chat_id, text='Dieser Kanal existiert nicht!', reply_to_message_id=update.message.message_id)
        return
      rss_list = get_rss_list(str(chat_info.id), chat_info.title)
    else:
      if update.message.chat.first_name:
        chat_name = update.message.chat.first_name
      else:
        chat_name = update.message.chat.title
      rss_list = get_rss_list(str(update.message.chat_id), chat_name)
    bot.sendMessage(
                    chat_id=update.message.chat_id,
                    text = rss_list,
                    reply_to_message_id=update.message.message_id,
                    parse_mode=ParseMode.HTML
                   )

def get_new_entries(last, nentries):
    entries = []
    for k,v in enumerate(nentries):
      if v.id == last:
        return entries
      else:
        entries.append(v)
    return entries

def manually_check_rss(bot, update):
    if not can_use(update):
      return
    check_rss(bot, '')
    bot.sendMessage(
                    chat_id=update.message.chat_id,
                    text = 'Ausgeführt.',
                    reply_to_message_id=update.message.message_id
                   )

@run_async
def check_rss(bot, job):
    keys = list(r.keys('pythonbot:rss:*:subs'))
    for k, v in enumerate(keys):
      p = re.compile('pythonbot:rss:(.+):subs')
      match_func = p.search(v)
      url = match_func.group(1)
      print('RSS: ' + url)
      last = r.get('pythonbot:rss:' + url + ':last_entry')

      feed_data = feedparser.parse(url)
      if not 'title' in feed_data.feed:
        feed_title = feed_data.feed.link
      else:
        feed_title = feed_data.feed.title
      newentr = get_new_entries(last, feed_data.entries)
      text = ''
      for k2, v2 in enumerate(newentr):
        if not 'title' in v2:
          title = 'Kein Titel'
        else:
          title = v2.title
        if not 'link' in v2:
          link = feed_data.feed.link
          link_name = link
        else:
          link = v2.link
          link_name = urlparse(link).netloc
        if 'summary' in v2:
            content = cleanRSS(v2.summary)
            content = remove_tags(content).lstrip()
            if len(content) > 250:
              content = content[0:250] + '...'
        else:
            content = ''
        # Für 1 Nachricht pro Beitrag, tue dies:
        # Entferne hier das "text + "...
        text = text + '\n<b>' + title + '</b>\n<i>' + feed_title + '</i>\n' + content + '\n<a href="' + link + '">Auf ' + link_name + ' weiterlesen</a>\n'
      # ...und setze hier vor jeder Zeile 2 zusätzliche Leerzeichen
      if text != '':
        newlast = newentr[0].id
        r.set('pythonbot:rss:' + url + ':last_entry', newlast)
        for k2, receiver in enumerate(list(r.smembers(v))):
          try:
            bot.sendMessage(receiver, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
          except Unauthorized:
            print('Chat ' + receiver + ' existiert nicht mehr, lösche aus Abonnenten-Liste')
            r.srem(v, receiver)
            r.delete('pythonbot:rss:' + receiver)
          except ChatMigrated as e:
            print('Chat migriert: ' + receiver + ' -> ' + str(e.new_chat_id))
            r.srem(v, receiver)
            r.sadd(v, e.new_chat_id)
            r.rename('pythonbot:rss:' + receiver, 'pythonbot:rss:' + str(e.new_chat_id))
            bot.sendMessage(e.new_chat_id, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)            
    print('----------')

def error(bot, update, error):
    logger.warn('Update "%s" verursachte Fehler "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=config['DEFAULT']['token'])
    j = updater.job_queue
    
    # Bot-Infos prüfen
    bot_info = updater.bot.getMe()
    print('Starte ' + bot_info.first_name + ', AKA @' + bot_info.username + ' (' + str(bot_info.id) + ')')

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("hilfe", help))
    
    dp.add_handler(CommandHandler("rss", list_rss, pass_args=True))
    dp.add_handler(CommandHandler("sub", subscribe_to_rss, pass_args=True))
    dp.add_handler(CommandHandler("del", unsubscribe_rss, pass_args=True))
    dp.add_handler(CommandHandler("sync", manually_check_rss))

    # log all errors
    dp.add_error_handler(error)
    
    # cron
    job_minute = Job(check_rss, 60.0)
    j.put(job_minute, next_t=10.0)

    # Start the Bot
    updater.start_polling(timeout=20, clean=True)

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()