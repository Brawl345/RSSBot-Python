#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import html
import re

from bot import admins


def can_use_bot(update):
    """Returns True if user is an admin"""
    if update.message.from_user.id in admins:
        return True
    else:
        return False


def get_new_entries(entries, last_entry):
    """Returns all new entries from an entries dict up to the last new article"""
    new_entries = []
    for entry in entries:
        if 'id' in entry:
            if entry['id'] == last_entry:
                return new_entries
            else:
                new_entries.append(entry)
        else:
            if entry['link'] == last_entry:
                return new_entries
            else:
                new_entries.append(entry)
    return new_entries


def remove_html_tags(rawhtml):
    """Removes HTML tags"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', rawhtml)
    return cleantext


def clean_rss(content):
    """Cleans content"""
    content = content.replace('[…]', '')
    content = content.replace('[bilder]', '')
    content = content.replace('[boerse]', '')
    content = content.replace('[mehr]', '')
    content = content.replace('[video]', '')
    content = content.replace('...[more]', '')
    content = content.replace('[more]', '')
    content = content.replace('[liveticker]', '')
    content = content.replace('[livestream]', '')
    content = content.replace('[multimedia]', '')
    content = content.replace('[sportschau]', '')
    content = content.replace('[phoenix]', '')
    content = content.replace('[swr]', '')
    content = content.replace('[ndr]', '')
    content = content.replace('[mdr]', '')
    content = content.replace('[rbb]', '')
    content = content.replace('[wdr]', '')
    content = content.replace('[hr]', '')
    content = content.replace('[br]', '')
    content = content.replace('Click for full.', '')
    content = content.replace('Read more »', '')
    content = content.replace('Read more', '')
    content = content.replace('...Read More', '')
    content = content.replace('(more…)', '')
    content = content.replace('View On WordPress', '')
    content = content.replace('Continue reading →', '')
    content = content.replace('(RSS generated with  FetchRss)', '')
    content = content.replace('-- Delivered by Feed43 service', '')
    content = content.replace('Meldung bei www.tagesschau.de lesen', '')
    content = content.replace('<', '&lt;')
    content = content.replace('>', '&gt;')
    content = re.sub('Der Beitrag.*erschien zuerst auf .+\.', '', content)
    content = re.sub('The post.*appeared first on .+\.', '', content)
    content = re.sub('http://www\.serienjunkies.de/.*\.html', '', content)
    return content


def get_content(content):
    """Sanitizes content and cuts it to 250 chars"""
    content = clean_rss(remove_html_tags(html.unescape(content)).strip())
    if len(content) > 250:
        content = content[0:250] + '...'
    return content
