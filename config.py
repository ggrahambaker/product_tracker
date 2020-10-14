import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'never-guesses'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    S3_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    S3_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
    

    ADMINS = ['pd_tracker@solution4u.com']
    POSTS_PER_PAGE = 10
    UPLOAD_EXTENSIONS = ['.jpg', '.png', '.pdf', '.doc', '.docx', '.txt']
    MAX_CONTENT_LENGTH = 1024 * 1024
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')



