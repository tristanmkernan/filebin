# FileBin

*Like PasteBin, but for files*

![main](screenshots/main.png?raw=true)
---
![main](screenshots/bin.png?raw=true)

## Setup

```
make # short for make build
make irun # run in interactive mode
make drun # run as daemon
make stop # stop daemon
```

Then point your browser at http://localhost:$some_local_port.

## Motivation

- To make it easier to send files between phone and desktop - why do I still use e-mail for this?
- To deploy a Flask application using Docker.

## Stack

#### Frontend

- [Bulma](https://bulma.io/) _MIT_
- [Font Awesome](https://fontawesome.com/v4.7.0/) _CC BY 4.0_ and _SIL OLF_
- [jQuery](https://jquery.com/) _MIT_

#### Backend

- [Flask](http://flask.pocoo.org/) _three clause BSD License_

#### Others

- [NLTK](https://www.nltk.org/) _apache 2.0_
- [WordNet](https://wordnet.princeton.edu/) _[here](https://wordnet.princeton.edu/license-and-commercial-use)_
- [uwsgi-nginx-flask](https://github.com/tiangolo/uwsgi-nginx-flask-docker]) _Apache 2.0_
- [GIMP](https://www.gimp.org/)

## License

GPL
