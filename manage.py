#!python2
import os
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from app import app, db

app.config.from_object(os.getenv('APP_SETTINGS', "config.DefaultConfig"))

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

manager.add_command('runserver', Server(
    use_debugger=os.getenv('DEBUG_MODE', True),
    use_reloader=os.getenv('FLASK_RELOADER', True),
    threaded=True,
))

if __name__ == '__main__':
    manager.run()
