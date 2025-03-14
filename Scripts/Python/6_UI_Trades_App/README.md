# UI - IFT BIG DATA


## HOW TO?

The app relies on the assumption that it runs behind a proxy server to manage authentication.

The proxy auth redirects traffic to this application and builds headers that are then used to check permissions within the website.

In order to mimick this behaviour on your browser, it is reccommended to install the modify headers extension and add the following:

```
X-Forwarded-Email: n.surname@ucl.ac.uk
X-Forwarded-Groups: ift-scarp-admin
```

```bash

poetry run uvicorn main:app --port 8100 --reload

```