import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///math.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
