class Config:
    SECRET_KEY = 's3cr3t_very_long_and_random_string_1234567890'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # Для розробки, згодом можна перейти на PostgreSQL або MySQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
