from flask import Flask, session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os
db=SQLAlchemy()
#DB_NAME = "database.db"
mail = Mail()
def create_app():
    app = Flask(__name__, static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static')),
        static_url_path='/static')
    app.config['SECRET_KEY'] = 'PCTMConst'
    # ✅ Full absolute path to ensure SQLite writes to correct DB
    #db_path = os.path.join(app.instance_path, 'database.db')
    #app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://myuser:mypassword@localhost:5432/mydb"
)

    app.config.update(
        
        #MAIL_SERVER='smtp.gmail.com',
        MAIL_SUPPRESS_SEND=True
        #MAIL_PORT=587,
        #MAIL_USE_TLS=True,
        #MAIL_USERNAME='andreacolon@pctmconstruction.com',
        #MAIL_PASSWORD='botr uiqj ukwg jomn',
        #MAIL_DEFAULT_SENDER='petty-do-not-reply@pctmconstruction.com'
    )
    mail.init_app(app)  # initialize Mail with app

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix = '/')
    app.register_blueprint(auth, url_prefix = '/')

    from .models import User, Equip, Dispatch, Return, DailyLog, Projects, Images, Training, TrainingLog, Traindocs, Names, EquipSeguridad, EquipSeguridadDisp, Incidentes, Incidentesdocs, PettyCash, PettyCashItems, PettyCashItemsDocs, Materials, MaterialsDisp


    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    @app.context_processor
    def inject_username():
        return dict(username=session.get('userName'))

    return app
