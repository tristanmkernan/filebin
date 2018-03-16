# FileBin

*Like PasteBin, but for files*

![main](screenshots/main.png?raw=true)
![main](screenshots/bin.png?raw=true)

## Setup

```
docker build -t your_tag .
docker run -it -p $some_local_port:80 your_tag
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

- [English Language Dictionary JSON](https://github.com/adambom/dictionary]) _MIT_
- [uwsgi-nginx-flask](https://github.com/tiangolo/uwsgi-nginx-flask-docker]) _Apache 2.0_
- [GIMP](https://www.gimp.org/)

## License

GPL
