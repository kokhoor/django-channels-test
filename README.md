Django Channels
===
Demo files for the talk I gave in #pyconmy2016.
Slides can be accessed here: http://www.slideshare.net/kokhoor/pyconmy-2016-django-channels

Assumption(s):
You will need to setup your own virtual environment as necessary

How To:
---
1. Install requirements

    ```
    $ pip install -r requirements.txt
    ```

2. Initial Setup

    ```
    $ python manage.py migrate
    ```

    To create your super user

    ```
    $ python manage.py createsuperuser
    ```

3. Browse to admin (You need to start the server first), and create rooms first before you can use chat feature (http://localhost:8000/admin/)

4. To run single channels layer example (refer to channels_test/settings.py)

    ```
    $ redis-server
    $ python manage.py runserver
    $ python manage.py runworker send-email

    ```

    You can add additional workers (as many as you like)
    ```
    $ python manage.py runworker
    ```

5. To run single channels layer with sharding example (refer to channels_test/settings_sharding.py)

	```
	$ redis-server
	$ redis-server --port 7777
	
	$ daphne -b 0.0.0.0 -p 8000 main.asgi_sharding:application
	
	$ python manage.py runworker --settings channels_test.settings_sharding send-email
	$ python manage.py runworker --settings channels_test.settings_sharding send-email
	```

6. To run the multiple channels layer example ('test' layer and 'chat' layer) - refer to channels_test/settings_prod.py)

   The running of two daphne no longer so helpful now because I believe websocket now linked to daphne instance,
   so it seems both port 8000 and 8080 will host the http and websocket.
	```
	$ redis-server
	$ redis-server --port 7777
	
	$ daphne -b 0.0.0.0 -p 8000 main.asgi_test:application
	$ python manage.py runworker --settings channels_test.settings_prod --layer test send-email
	$ python manage.py runworker --settings channels_test.settings_prod --layer test send-email
	
	$ daphne -b 0.0.0.0 -p 8080 main.asgi_chat:application
	```
