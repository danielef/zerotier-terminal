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

def get_member_status(member):
    member_name = member.get('name', '')
    member_cfg  = member.get('config', {'ipAssignments': ['no-valid-ip'], 'authorized': False})
    member_ip =  member_cfg.get('ipAssignments')[0] if len(member_cfg.get('ipAssignments')) > 0 else member.get('physicalAddress','unknown')
    if member_cfg.get('authorized') is not True:
        return {'member_color': curses.color_pair(5), 'member_name': 'unauthorized', 'member_ip': member_ip}
    elif member.get('online', False):
        return {'member_color': curses.color_pair(2), 'member_name': member_name, 'member_ip': member_ip}
    else:
        return {'member_color': curses.color_pair(4), 'member_name': member_name, 'member_ip': member_ip}

def main():
    window = curses.initscr()
    curses.noecho() # prevents user input from being echoed

    curses.start_color()
    curses.use_default_colors()

    h,w = window.getmaxyx()
    stdscr = curses.newpad(h,w)
    key_pressed = ''
    mypad_pos = 0
    
    curses.init_pair(1, curses.COLOR_WHITE,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLUE,   curses.COLOR_BLACK)

    try:
        networks = {}
        ts_success = ''
        while True:
            h,w = window.getmaxyx()
            stdscr.refresh(mypad_pos, 0, 0, 1, h-1, w-1)
            stdscr.clear()
            ts = time.localtime()
            dt = time.strftime('%H:%M:%S', ts)
            if ts.tm_sec % 30:
                try:
                    for network in retrieve_networks(zerotier_token):
                        network_id = network.get('id')
                        network_name = network.get('config', {}).get('name')
                        networks[network_id] = (network_name,
                                                sorted(retrieve_members(network_id, zerotier_token), key=lambda m: m['name']))
                    ts_success = dt
                except Exception as e:                
                    stdscr.addstr(0, 0, '???',  curses.color_pair(3))
                    stdscr.addstr(0, 2, '{} connection lost!'.format(ts_success),  curses.color_pair(1))

            #time.sleep(1)
            i = 1

            for x,(name,members) in networks.items():
                stdscr.addstr(i, 0, '???',  curses.color_pair(2))
                stdscr.addstr(i, 2, '{} : {}'.format(name, len(members)), curses.color_pair(1))
                for y, member in enumerate(members):
                    member_status = get_member_status(member)
                    stdscr.addstr(i+1, 1, '???',  member_status.get('member_color'))
                    stdscr.addstr(i+1, 3, '{} {}'.format(member_status.get('member_name'), 
                                                         member_status.get('member_ip'), 
                                                         curses.color_pair(1)))
                    i=i+1
            stdscr.refresh(mypad_pos, 0, 0, 1, h-1, w-1)

            key_pressed = stdscr.getch()
            if key_pressed == (27 and 91 and 65):
                mypad_pos -= 1
            elif key_pressed == (27 and 91 and 66):
                mypad_pos += 1
            elif key_pressed == (27 and 91 and 53):
                mypad_pos -= h - 2
            elif key_pressed == (27 and 91 and 54):
                mypad_pos += h - 2

    except KeyboardInterrupt:
        stdscr.refresh(mypad_pos, 0, 0, 1, h-1, w-1)
    
    finally:
        stdscr.addstr(0, 0, '???',  curses.color_pair(3))
        stdscr.addstr(0, 2, 'quitting ...',  curses.color_pair(1))
        stdscr.refresh(mypad_pos, 0, 0, 1, h-1, w-1)
        time.sleep(1) # This delay just so we can see final screen output
        curses.endwin()

main()
#curses.wrapper(main)

