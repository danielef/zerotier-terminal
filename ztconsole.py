import curses
import json
import os
import ssl
import time
import urllib.request

zerotier_token=os.environ.get('ZEROTIER_TOKEN', None)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def retrieve_data(request,
                  token,
                  template_auth = 'bearer {}',):
    request.add_header('Authorization', template_auth.format(token))
    json_bytes = urllib.request.urlopen(request, context=ctx)
    return json.loads(json_bytes.read().decode('utf-8'))

def retrieve_networks(token,
                      template_url = 'https://my.zerotier.com/api/network',
                      template_auth = 'bearer {}'):
    request = urllib.request.Request(template_url)
    return retrieve_data(request, token, template_auth)

def retrieve_members(network_id, 
                     token, 
                     template_url = 'https://my.zerotier.com/api/network/{}/member',
                     template_auth = 'bearer {}'):
    request = urllib.request.Request(template_url.format(network_id))
    return retrieve_data(request, token, template_auth)

def main(stdscr):
    curses.init_pair(1, curses.COLOR_WHITE,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED,    curses.COLOR_BLACK)

    networks = {}
    while True:
        # Clear screen
        stdscr.clear()
        ts = time.localtime()
        dt = time.strftime("%H:%M:%S", ts)
        if ts.tm_sec % 10:
            try:
                for network in retrieve_networks(zerotier_token):
                    network_id = network.get('id')
                    networks[network_id] = sorted(retrieve_members(network_id, zerotier_token), key=lambda m: m['name']) 
            except Exception as e:
                stdscr.addstr(0, 0, '•',  curses.color_pair(3))
                stdscr.addstr(0, 2, '{} Connection error!'.format(dt),  curses.color_pair(1))
                #stdscr.refresh()
        time.sleep(1)

        i = 0
        for x,members in networks.items():
            for y, member in enumerate(members):
                color_status = curses.color_pair(2) if member.get('online', False) else curses.color_pair(4)
                member_name = member.get('name', '')
                member_cfg  = member.get('config', {'ipAssignments': ['no-valid-ip']})
                stdscr.addstr(i+1, 0, '•', color_status)
                stdscr.addstr(i+1, 2, '{} {}'.format(member_name, member_cfg.get('ipAssignments')[0]), curses.color_pair(1))
                i=i+1
        stdscr.refresh()

        #stdscr.getkey()

curses.wrapper(main)

