class Config:
    SECRET_KEY = 'ВАШ_СЕКРЕТНИЙ_КЛЮЧ'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mydatabase.db'  # Для розробки, згодом можна перейти на PostgreSQL або MySQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
