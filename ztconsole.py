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

def main():
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()

    stdscr = curses.newpad(40,60)
    mypad_pos = 0
    
    curses.init_pair(1, curses.COLOR_WHITE,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED,    curses.COLOR_BLACK)

    try:
        networks = {}
        ts_success = ''
        while True:
            size=os.get_terminal_size()
            stdscr.refresh(0, 0, 0, 1, size.lines-1, size.columns-1)
            stdscr.clear()
            ts = time.localtime()
            dt = time.strftime('%H:%M:%S', ts)
            if ts.tm_sec % 10:
                try:
                    for network in retrieve_networks(zerotier_token):
                        network_id = network.get('id')
                        network_name = network.get('config', {}).get('name')
                        networks[network_id] = (network_name,
                                                sorted(retrieve_members(network_id, zerotier_token), key=lambda m: m['name']))
                    ts_success = dt
                except Exception as e:                
                    stdscr.addstr(0, 0, '•',  curses.color_pair(3))
                    stdscr.addstr(0, 2, '{} connection lost!'.format(ts_success),  curses.color_pair(1))

            time.sleep(1)
            i = 1

            for x,(name,members) in networks.items():
                stdscr.addstr(i, 0, '•',  curses.color_pair(2))
                stdscr.addstr(i, 2, '{} : {}'.format(name, len(members)), curses.color_pair(1))
                for y, member in enumerate(members):
                    color_status = curses.color_pair(2) if member.get('online', False) else curses.color_pair(4)
                    member_name = member.get('name', '')
                    member_cfg  = member.get('config', {'ipAssignments': ['no-valid-ip']})
                    stdscr.addstr(i+1, 1, '•', color_status)
                    stdscr.addstr(i+1, 3, '{} {}'.format(member_name, member_cfg.get('ipAssignments')[0]), curses.color_pair(1))
                    i=i+1
            stdscr.refresh(0, 0, 0, 1, size.lines-1, size.columns-1)

            if stdscr.getch() == ord('q'):
                break

    except KeyboardInterrupt:
        stdscr.refresh(0, 0, 0, 1, size.lines-1, size.columns-1)
    
    finally:
        stdscr.addstr(0, 0, '•',  curses.color_pair(3))
        stdscr.addstr(0, 2, 'quitting ...',  curses.color_pair(1))
        stdscr.refresh(0, 0, 0, 1, size.lines-1, size.columns-1)
        time.sleep(1) # This delay just so we can see final screen output
        curses.endwin()

main()
#curses.wrapper(main)

