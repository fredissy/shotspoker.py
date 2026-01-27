# Shots Poker

Free poker planning application

## Quickstart :

2 seconds run command-line :

`docker run -d -p5000:5000 fredissy/shots-poker:latest`

This will spin-up Shots Poker instance, running with in-memory store and embedded SQLite.

TODO : further options are available to use external PostgreSQL database or Redis store. 

## Screenshots :

Login Page :

![Login Page](/images/login.png)

Voting interface :

![Voting page](/images/voting.png)

Displaying results :

![Voting results](/images/results.png)

## Features :
* Room management
* Choosable card deck from 4 possibilities
* Instant client updates
* Observer mode, can be toggled on room joining and in-room
* Results chart
* Estimations queue management
* Session history by room
* Session timer
* Hidden easter-egg emoji reaction panel

## Tech stack :
* Backend : Python >=3.14, Flask, Redis, SQLite/PostgreSQL
* Frontend : Bootstrap, html 5

## Development guide

1. Clone the repository :

```git clone https://github.com/fredissy/shots-poker.git```

```cd shots-poker```

2. Install depdencies :

`pip install -r requirements.txt`

Update to .env file to fit your needs. To run the app without external PostgreSQL or Redis, comment `DATABASE_URL` and `REDIS_URL` environment variables.

3. Initialize database :

`flask db upgrade`

4. Run the app :

```python app.py```


## Contributions

Pull requests are welcome!

## Licence

GNU LGPLv3
