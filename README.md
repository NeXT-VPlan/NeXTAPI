# NeXTPlan API

## Introduction
NeXTPlan API is a simple API "Frontend" to the - frankly, horrible - Stundenplan24 "API". This API aims to improve the many flaws of the Stundenplan24 API, such as the lack of a proper documentation, the lack of a proper error handling and the lack of a proper, up-to-date response format.

## Self-Deployment
To deploy the API on your own server, you need to have a working installation of Python and pip. After you have installed these, you can clone the repository and install the dependencies by running the following commands:
```bash
pip install -r requirements.txt
python -c 'from app import app, db; app.app_context().push(); db.create_all()'
```

After you have installed the dependencies, you can start the API by running the following command:
```bash
python run.py --port [PORT]
```

