List all visited messages in Mattermost from a past time range, no matter in which channel they were.

TODO:

- [ ] proper docs
- [ ] Color the output, randomly colorize each channel differently
  - random.seed(channel_name)
- [ ] maybe some kind of interactivity

```
. ./bin/activate
./mattermost-history.py
```

It will ask for a start date aswell as a delta.
Then it will fetch messages *from all chats* within this time period and show it chronologically.
