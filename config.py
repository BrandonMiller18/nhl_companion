"""Flask configuration"""
import os

SECRET_KEY = os.environ.get("SECRET_KEY")