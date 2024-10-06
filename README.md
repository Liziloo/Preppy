# Preppy APP
## Description:

Preppy is a self-hosted, dockerized flask app to aid households with emergency preparedness, as recommended by the American federal government and Red Cross. It helps users create customized task and supply lists, keep track of medical and emergency contact information, track routine schedules, determine emergency meet-up locations and securely store important documents, such as copies of drivers' licenses and passports.

### Front-End

The app front-end is an HTML, CSS and Javascript website. I used a BootSwatch theme for Bootstrap because I am not aesthetically inclined, so that made visual choices easier.

The user must first enter basic information about their household in an html form. This information is used to help guide all other sections of the app. All other navigational links redirect to this form until the user has filled in all necessary information. As of this writing, some of the requested information is not yet incorporated into the app. At a future date, I intend to improve the customized suggestions in the other parts of the app based on such things as whether anyone in the household has any special needs, and updating the suggested amounts of supplies based on the number of residents.

The next three sections of the app guide users in building customized checklists of tasks to do and supplies to gather for sheltering in place and gobags. Task and supply suggestions are made based on the user's state of residence and the specific types of disasters for which they would like to be prepared. Users can also add their own custom supplies and tasks. Checklists are printable.

The Medical section consists of forms for users to enter basic medical information about the members of their household, as well as the contact information for their medical providers. Similarly, the Emergency Contacts section allows users to store addresses, phone numbers and emails that they might need in an emergency. As information is entered by the user, it is added to a database and displayed in printable tables in the app.

The Meet-Up Locations section incorporates the Google Maps Javascript API to provide an interactive map. The map can be used to store pins indicating locations where household members may plan to meet up in case of an emergency making their home area unsafe. It is automatically centered on the user's home state. Pin coordinates and labels are stored in the local database and incorporated into a printable table.

The Routines section is intended for use in keeping track of household members' habitual schedules and locations throughout the week. This may aid in quickly tracking down a household member in the event of a n emergency. The app incorporates the FullCalendar API to provide calendar functionality. The calendar is clickable and printable, allowing users to add and edit events. It is also color coded, with each household member listed by the user receiving a random color.

Finally, the Secure Documents section provides a way for users to upload copies of important documents and store them in a digital, encrypted format. The files can then be downloaded and printed as needed.

### Back-End

The app back-end consists of multiple python files and a SQLAlchemy sqlite database. The main [app.py](./app.py) file sets up functionality used by all other files, including the database, mail server, error logging, CSRF and CSP security features. It also contains the route to the index page. The [auth_routes.py](./auth_routes.py), [data_routes.py](./data_routes.py), [supply_routes.py](./supply_routes.py), [task_routes.py](./task_routes.py) and [userinfo_routes.py](./userinfo_routes.py) files contain the other primary app routes. The blueprints for these files are registered in the main app.py file. I divided the routes into multiple python files to aid readability and organization.

[Helpers.py](./helpers.py) and [utils.py](./utils.py) contain helper functions used by the other routes. The [dbmodels.py](./dbmodels.py), [preppydb.py](./preppydb.py) and [init_db.py](./init_db.py) files define the database models and create the database, pulling from the various .csv files for initial data when a new docker instance of the app is launched.

I use Alembic to make changes to the database schema. The [alembic folder](./alembic) contains the necessary files for this. This will make future versioning of the app easier.

The static files are subdivided into [css](./static/css), [images](./static/images) and [js](./static/js) for organizational purposes. Almost every html page has its own linked javascript file providing much of the on-page functionality. The image files are simply favicons to play nice with different browsers.

### Docker

I decided to dockerize the Preppy app because I run multiple open-source dockerized apps on my own home server that I set up in January when I first became interested in programming. I would like to provide others access to this app, should anyone deem it worthwhile to run, as I have benefited greatly from others' work on similar apps. Running a self-hosted instance of my app on a home server would also mean that users can store all the data they enter securely, so long as they follow best practices for accessing their server. Dockerizing the app also means that someone should be able to run it safely without affecting the rest of their system, despite my lack of programming experience.

The Preppy app docker image is created using the [Dockerfile](./Dockerfile) and [docker-compose.yml](./docker-compose.yml) files, as well as a user-provided .env file. I've provided an [example .env](./example.env) file with details of what needs to be included. This file is necessary to securely provide API keys, email credentials and other senstive data needed for full app functionality. As of right now, to run the app, a user should:
1. Install docker and docker compose on their system
2. Clone the Preppy app repository
3. Edit the example.env file to provide their own credentials
4. Rename example.env to simply .env
4. Run docker-compose up within the repository to start the app

My intention is to upload an image to DockerHub. When I've done that, the user would no longer need to clone the repository, but instead simply run the app using a docker compose file and .env file. But since I've never made a public docker image before, right now my image is private on DockerHub.

### License

This project is licensed under the terms of the [GPL v3 License](./LICENSE.txt).

I personally use quite a bit of software from open-source projects, so I decided to make my project open-source as well. Also, the FullCalendar licensing terms require compliance with the GPLv3 license.

## Credits
- Calendar functionality provided by [FullCalendar](https://fullcalendar.io/)
- Front-end framework provided by [Bootstrap](https://getbootstrap.com/)
- Maps and address search provided by [Google Maps API](https://developers.google.com/maps). Thanks to Google Gemini for help with this.
- Theme by [Bootswatch](https://bootswatch.com/)
- Thanks to [Miguel Grinberg](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-vii-error-handling) for information on error handling.
