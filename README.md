# tbot
A telegram bot 

## What is this?
This is a Telegram bot that responds to commands. At the moment it has some toy features which build out the infrastructure required for a more serious application.

## Ok what features does it support?
- Echo text. It just echoes whatever you send it.
- Send a quote. It will send a random quote in the chat window.
- Convert video file. Supply it with a *cough* yt video url, then it will download the file convert it to mp3 and send you an email that the file is ready.
- Facial recognition. Train the bot to recognise a face from a photo and it will do so in future.
- Reddit integration. For the quotes table get reddit content from my favourite subreddits (text and pictures supported) at fixed scheduled. 
- Maybe this is a different app, but the feature I'm working on now involves web scraping share prices from the JSE and using the bot to quote actionable information, and the task queuing system to do offline analysis of the data.

## How do you get it right?
- I am using the Telegram Bot API for this. My application is hosted on a Raspberry Pi 3, written in Python 3 (python-flask) and the ssl certificate is provided by letsencrypt. I am using the duckdns dynamic IP resolution service. I am using MariaDB/Mysql as the backend database.
- In the flask-api I am using flask-restful-api to manage the api interface for the quotes (not really needed but I needed a way to enter data into the database and for that postman is used).
- Because the video processing operation is best done as an asynchronous task (meaning unlike asking for a quote locking up a server thread while waiting for the processing thread to complete is bad practise) I am using a task processor called Celery. It uses redis as the backing store. Redis itself is run as a docker image.
- Notification emails are sent as a task (originally that part of the infrastructure was written because a security alert it sent out everytime there's an ssh login on the RasPi and doing that sychronously slows login). 

## How do you get it right x 2?
- Yea, you really don't need a static ip address to get an ssl certificate.
- I use python virtualenv to keep things clean so pip3 is used to track and install dependencies.
- Configuration values are read from the config file using the config class pattern, but the actual values are read from the environment using pyenv (the .env file for this doesn't get checked into source control).
- I have integrated the celery tasks with the flask instance but the worker process itself has to run in a seperate process.
- On the public facing server (required for when Telegram sends your bot updates), I run apache2 with mod_wsgi.
- I take care of logging using the python logging library.
- You get a chat message when then long running tasks are completed. And a link to the hosted file. Unfortunately you won't be able to convert videos through the public deployment as that requires authorisation from me. But you can change the code yourself when you deploy it.

## How do you get it right x3?
- I have a task processing framework that already supports useful features. Main features are download web page, scrape data, query database, send notification and prompt and react accordingly.
- Users can interact with an application they might already have namely an instant messenger app through a bot (so possibly zero-install).

## So you're a developer?
- Sorry, I'm actually a C# developer so PEP8 standards are not applied. My class names sometimes look like C# class names. But who cares, right?

## What's the plan ahead?
- If you didn't notice it, there's no reason for the video file to be converted to mp3. It's just the driver for that requirement is somebody keeps asking me to `download that song`. What should actually be happening is you should be able to tell the bot the url (which doesn't have to be YouTube by the way) and specify the output format you're after. [DONE]
- I have to decide between sending the file as an audio attachment to the chat, or as an email. At the moment I pick it up from the processing folder by uploading it via my nextcloud. Let's just say there are complications doing it any other way. [DONE - it will send a url to a self-hosted file in the chat which initiated the conversion]
- Face recognition. Send the bot a photo and it will recognise all known faces in the photo. Send a photo to learn and it will label the first face it sees. [DONE]
- Do not overwrite the label of the first face it sees. Meaning, even though the bot has a definition of the face it's still possible to tell it to relearn the face. It would be possible to relearn a known face and a face will have multiple names then. Also users can overwrite names. [CANCELLED]

## Where can I see it?
- Install the software described here, I've included all the source code but you'll need to create a configuration file based off the sample. You will need to get your own API-keys (currently only for Reddit and the Telegram Bot Api)

## KNOWN ISSUE
- There are some issues with the bot api library I'm used and might have to swap it out for something else. Under conditions of high load it appears some next_step handlers get overwritten.
