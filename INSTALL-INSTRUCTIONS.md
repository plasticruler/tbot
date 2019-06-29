
Install is somewhat complex but you only need to do it once. 

# Component list
- A raspberry pi. Ok maybe not, but doesn't that just sound sexy? My instance runs off a RasPi 3.
- Ubuntu/Debian. It will not work on Windows as Celery is no longer supported on that platform.
- Python 3.5+
- Apache2
- Supervisor (to run celery/beat as a daemonized process)
- MySQL / MariaDB
- Celery 
- Redis (as a docker image is fine)
- A Gmail account
- A Telegram account
- A reddit account
- A duckdns account
- A letsencrypt account
- Ok, also a docker account.

# Install instructions
## Python environment
+  Install `pip3` and `virtualenv`. Then install required packages using the requirements.txt file. `pip3 install -r requirements.txt`

+ Ensure correct packages have been installed. It takes a while to build `dlib` and there are probably other packages/application you have to install first (eg. `PIL` and `Pillow`)

## Configuration

+ Make a copy of `default.env` and name it `.env`. Update the entries to your situation. This is the most complicated part of installation because it involves signing up for a Telegram Bot account using `@botfather`, as well as obtaining reddit API keys.

## Database
+ Create the database `tbot` with username and password.

## Telegram Bot
### Registering your bot
+ The telegram servers will only call your webhooks over SSL. So you'll need an ssl-certificate and a domain.

### duckdns dynamic DNS
+ Because I don't have a static IP address I use a dynamic dns service which resolves a static domain name to my dynamic ip address. 
+ Ensure that on your router you have opened ports `80` and `443` to the outside world. If you've set up apache correctly you will see the default pages. 

### letsencrypt certficate
+ To get a free SSL/letsencrypt certificate you will need a domain. There is a helpful script call `certbot` which can automatically set this up for you if you are using apache. Google this.

## Flask app
+ You will need to configure apache to activate your `virtualenv` environment and execute your flask application within that context. This is nicely done using the file `tbot.wsgi` that is dependent on the `mod_wsgi` apache add-on. You will have to configure a URI that your application will served from in one or more apache `*.conf` files. This can be very frustrating to configure correctly if you also have some PHP scripts or static content you want to run at the same time.

## Reddit API
+ To get subreddit content via the API you will need a reddit account to get necessary API keys. Just google how.

## Celery
+ This is a asynchronous task processor. The reason you need `redis` here is because task commands are serialized to redis (as opposed to rabbit-mq). Just use a docker image for redis. To manage my redis instance I use Redis Desktop Manager which is free for Linux desktops. Of course to get a redis instance running the first place I use docker.

## Supervisor
+ Because the celery processes are usually run as windowed processes which have to be restarted when your server crashes/reboots, we use supervisor to restart them. It also provides a nice UI where we can view log files associated with our celery processes.

+ In the `configs\conf.d` folder update the `*.conf` files as required. Make sure that the file `virtualenv_cmd.sh` has `+x` privileges. Do that by `chmod +x virtualenv_cmd.sh`. The latter script ensures that we can activate our `virtualenv` environment and then starts our `celery` processes inside the required directory. Note that the celery work and beat functionality must be executed from within the tbot folder so that python can correctly resolve the app import. Copy the `*.conf` files using `sudo cp *.conf /etc/supervisor/conf.d/`

## File permissions for image folder
+ We write photos sent to the bot to a folder, which is then scanned for faces. The `www-data` user will write these files if this is what apache has been configured to run under, but whatever user `celery` runs under will read them, so you can't use `/tmp` for that and must thefore set this up manually. 

## Validate your deploy
+ TODO
