#!/usr/bin/env python

import mattermost
import bisect
from datetime import datetime, timedelta

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
# Convert both begin and end to timestamp with microseconds
end = (datetime.timestamp(begin + timedelta(hours=delta))) * 1000
begin = datetime.timestamp(begin) * 1000

mm_server = input("Please enter the MM instance (e.g. 'chat.mattermost.com') \n # ")
mm_server = 'https://' + mm_server + '/api'
mm = mattermost.MMApi(mm_server)
bearer = input("Please Enter the bearer (Login in the browser, open dev tools->Storage, search MMAuthCookie)\n # ")
mm.login(bearer=bearer)

user = mm.get_user()
uid = user['id']

team = mm._get("/v4/users/me/teams")[0]
tid = team['id']

channels = mm.get_channel_memberships_for_user(uid, tid)
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
            c = mm.get_channel(channel)
            # We have a user channel
            if c['display_name'] == '':
                users = c['name'].split('__')
                if users[0] == uid:
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
            for u in mm.get_users_by_ids_list(list(self._users)):
                self.userMap[u['id']] = u['username']
                self._users.remove(u['id']) # no need to ever add them again
        return self.userMap[uid]

    def __str__(self):
        t = ""
        for m in self.messages:
            t += f"{datetime.fromtimestamp(m['timestamp']/1000)} {self.get_channel(m['channel'])}  {self.get_user(m['user'])}      {m['message'].split('\n')[0]}\n"

        return t

#    def __repr__(self):
#        for m in self.messages:
#            print(datetime.fromtimestamp(m['timestamp']), self.get_user(m['user']), m['message'])


messages = Messages()

for channel in channels:
    if channel['last_viewed_at'] > begin:
        posts = mm.get_posts_for_channel(channel['channel_id'])
        first_msg = True
        for post in posts:
            if post['create_at'] < begin and first_msg:
                break
            first_msg = False
            if post['create_at'] > end:
                continue
            messages.append({'timestamp': post['create_at'],
                             'user': post['user_id'],
                             'message':post['message'],
                             'channel':channel['channel_id']})
            # Break afterwards to get one message before beginning as context
            if post['create_at'] < begin:
                break


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
