#!/usr/bin/env python

import requests
import bisect
from datetime import datetime, timedelta
import pprint

# from datetime import datetime as dt
#print(calendar.month(dt.today().year, dt.today().month))
print("Please Enter the date you want to the first message from")
print("Default is always today")
year = input('Enter a year: ')
if year == '':
    year = datetime.now().year
else:
    year = int(year)
month = input('Enter a month: ')
if month == '':
    month = datetime.now().month
else:
    month = int(month)
day = input('Enter a day: ')
if day == '':
    day = datetime.now().day
else:
    day = int(day)
hour = input('Enter the hour: ')
if hour == '':
    hour = datetime.now().hour
else:
    hour = int(hour)
delta = input('Enter the delta in hours (e.g. 5 to print 5 hours of messages since start date):\n # ')
if delta == '':
    delta = 10
else:
    delta = int(delta)

begin = datetime(year, month, day, hour, 0, 0)
# NOT: Convert both begin and end to timestamp with microseconds
end = (datetime.timestamp(begin + timedelta(hours=delta)))# * 1000
begin = datetime.timestamp(begin) #* 1000

mm_server = input("Please enter the MM instance (e.g. 'chat.mattermost.com') \n # ")
mm_server = 'https://' + mm_server + '/api/v4/'
#mm = mattermost.MMApi(mm_server)
bearer = input("Please Enter the bearer (Login in the browser, open dev tools->Storage, search MMAuthCookie)\n # ")
#mm.login(bearer=bearer)
headers = {
        'Authorization': "bearer " + bearer,
}

user_id = requests.get(mm_server+'users/me', headers=headers).json()['id']
team_id = requests.get(mm_server+'users/me/teams', headers=headers).json()[0]['id']
channels = requests.get(mm_server+'users/'+user_id+'/teams/'+team_id+'/channels/members', headers=headers)
#channel_ids = [ channel['channel_id'] for channel in channels.json() ]

def clear_line():
    LINE_CLEAR = '\x1b[2K'
    print(LINE_CLEAR, end= '\r')

def info(m):
    clear_line()
    print(m, end = '\r')

class Messages():
    '''
    Store a list of mattermost messages in timestamp order from multiple channels
    '''
    def __init__(self):
        self.messages = []
        self._users = set()
        self.channels = set()
        self.channelMap = {}
        self.userMap = {}

    def append(self, el):
        self.add_user(el['user'])
        bisect.insort(self.messages, el, key=lambda x: x['timestamp'])

    def get_channel(self, channel):
        if channel not in self.channelMap:
            #c = mm.get_channel(channel)
            c = requests.get(mm_server+'channels/'+channel, headers=headers).json()
            # We have a user channel
            if c['display_name'] == '':
                users = c['name'].split('__')
                if users[0] == user_id:
                    u = users[1]
                else:
                    u = users[0]
                self.add_user(u)
                self.channelMap[channel] = self.get_user(u)

            # We have a group channel
            else:
                self.channelMap[channel] = c['display_name']
        return self.channelMap[channel]

    def add_user(self, uid):
        if uid not in self.userMap:
            self._users.add(uid)

    def get_user(self, uid):
        if uid not in self.userMap:
            for u in requests.post(mm_server+'users/ids', json=list(self._users), headers=headers).json():
                self.userMap[u['id']] = u['username']
                self._users.remove(u['id']) # no need to ever add them again
        return self.userMap[uid]

    def __str__(self):
        t = ""
        for m in self.messages:
            x = '\n'
            t += f"{datetime.fromtimestamp(m['timestamp']/1000)} {self.get_channel(m['channel'])}  {self.get_user(m['user'])}      {m['message'].split(x)[0]}\n"

        return t

#    def __repr__(self):
#        for m in self.messages:
#            print(datetime.fromtimestamp(m['timestamp']), self.get_user(m['user']), m['message'])



def get_messages(channel, messages):
    if channel['last_viewed_at'] > begin:
        next_id = "yes"
        page = 0
        while next_id != '':
            _posts = requests.get(mm_server+'/channels/'+channel['channel_id']+'/posts', headers=headers, params={'since': int(begin), 'page': page, 'per_page': 1000 })
            posts = _posts.json()
            # We can get a 403 error, probably when messages have been deleted, etc.
            # Ignore these channels.
            if 'status_code' in posts and posts['status_code'] == 403:
                break
            if 'posts' not in posts:
                try:
                    # Ignore archived channels
                    if posts.get('id') == 'api.user.view_archived_channels.get_posts_for_channel.app_error':
                        return
                    else:
                        # WTF?
                        print("The following channel has no posts?!")
                        pprint.print(channel)
                        print("posts:")
                        pprint.pp(posts)
                        break
                except:
                    print(_posts.text)
                    exit()
            found_post = False
            p = posts['posts'].values()

            # If there are no more posts, exit
            for post in p:
                created = int(post['create_at'])
                if created/1000 > end:
                    continue
                if created/1000 < begin:
                    continue
                found_post = True
                messages.append({'timestamp': created,
                                 'user': post['user_id'],
                                 'message':post['message'],
                                 'channel':channel['channel_id']})
            #pprint.pp(posts)
            next_id = posts['next_post_id']
            page += 1

messages = Messages()
print("Going through channels")
print()
for channel in channels.json():
    info("Channel: "+requests.get(mm_server+'channels/'+channel['channel_id'], headers=headers).json()['display_name'])
    get_messages(channel, messages)

print("messages:")
print(messages)
#for m in sorted(messages, key=lambda x: x['timestamp']):
        #while True:
            #data_page = mm._get("/v4/channels/"+channel['channel_id']+"/posts", params={"page":str(page),"since":str(datetime.timestamp(d)*1000) })

#            if data_page['order'] == []:
#                break
#            page += 1
#            for order in data_page['order']:
#                print(data_page['posts'][order])



# Display:
#mm.get_users_by_ids_list([*map_user_ids_from_channels*])

# dt_object = datetime.fromtimestamp(timestamp)
