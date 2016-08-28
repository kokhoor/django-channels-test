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

    $ daphne -b 0.0.0.0 main.asgi:channel_layer

    $ python manage.py runworker
    ```

    You can add additional workers (as many as you like)
    ```
    $ python manage.py runworker
    ```

5. To run single channels layer with sharding example (refer to channels_test/settings_sharding.py)

	```
	$ redis-server
	$ redis-server --port 7777
	
	$ daphne -b 0.0.0.0 main.asgi_sharding:channel_layer
	
	$ python manage.py runworker --settings channels_test.settings_sharding
	$ python manage.py runworker --settings channels_test.settings_sharding
	```

6. To run the multiple channels layer example ('test' layer and 'chat' layer) - refer to channels_test/settings_prod.py)

	```
	$ redis-server
	$ redis-server --port 7777
	
	$ daphne -b 0.0.0.0 -p 8000 main.asgi_test:channel_layer
	$ python manage.py runworker --settings channels_test.settings_prod --layer test --only-channels http.request
	$ python manage.py runworker --settings channels_test.settings_prod --layer test --only-channels send-invite
	
	$ daphne -b 0.0.0.0 -p 8080 main.asgi_chat:channel_layer
	$ python manage.py runworker --settings channels_test.settings_prod --layer chat
	```
