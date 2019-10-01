# tbot
A telegram bot 

## What is this?
This is a Telegram bot that responds to commands. At the moment it has some toy features which build out the infrastructure required for a more serious application. At the moment it sends out personalisd content out every hour to subscribers with content tracking. It also supports ripping videos from online sources (currently only supports one populate site).

## Ok what features does it support?
- Echo text. It just echoes whatever you send it.
- Send a quote. It will send a random quote in the chat window.
- Convert video file. Supply it with a *cough* yt video url, then it will download the file convert it to mp3 and send you an email that the file is ready.
- Facial recognition. Train the bot to recognise a face from a photo and it will do so in future.
- Reddit integration. For the quotes table get reddit content from my favourite subreddits (text and pictures supported) at fixed scheduled. 
- Maybe this is a different app, but the feature I'm working on now involves web scraping share prices from the JSE and using the bot to quote actionable information, and the task queuing system to do offline analysis of the data. On command of `/chart STXNDQ` the bot returns below chart (based on the price information for the current day)

![alt text](https://raw.githubusercontent.com/plasticruler/tbot/master/chart.png)


## What's the plan ahead?
- See the project board

