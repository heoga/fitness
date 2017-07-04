import os


def find_phantomjs():
    phantom = os.environ.get('PHANTOMJS')
    if phantom:
        return phantom
    path_options = os.environ.get('PATH', '').split(os.pathsep)
    for path in path_options:
        for name in ('phantomjs', 'phantomjs.exe'):
            candidate = os.path.join(path, name)
            if os.path.exists(candidate):
                return candidate


def pytest_configure(config):
    from django.conf import settings

    MIDDLEWARE = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'reversion.middleware.RevisionMiddleware',
    )

    if 'TRAVIS' in os.environ:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'travisci',
                'USER': 'postgres',
                'PASSWORD': '',
                'HOST': 'localhost',
                'PORT': '',
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        }

    settings.configure(
        BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES=DATABASES,
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        TEMPLATES=[
            {
                'DIRS': [],
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
            },
        ],
        MIDDLEWARE=MIDDLEWARE,
        MIDDLEWARE_CLASSES=MIDDLEWARE,
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'rest_framework',
            'bootstrap3',
            'fitness.apps.FitnessConfig',
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
    )

    # guardian is optional
    try:
        import guardian  # NOQA
    except ImportError:
        pass
    else:
        settings.ANONYMOUS_USER_ID = -1
        settings.AUTHENTICATION_BACKENDS = (
            'django.contrib.auth.backends.ModelBackend',
            'guardian.backends.ObjectPermissionBackend',
        )
        settings.INSTALLED_APPS += (
            'guardian',
        )

    try:
        import django
        django.setup()
    except AttributeError:
        pass
    # Now configure PhantomJS
    if config.option.driver is None:
        config.option.driver = 'PhantomJS'
        config.option.driver_path = find_phantomjs()
