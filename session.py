import requests


def session_factory(session_settings):
    session = requests.Session()

    session_settings = session_settings.copy()
    for k, v in session_settings.pop('headers', {}).items():
        session.headers[k] = v

    for attr, value in session_settings.items():
        setattr(session, attr, value)

    return session
