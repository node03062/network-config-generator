# run.py

#
import os
from app import app, db
if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG_MODE', False)
    db.create_all()
    app.run(debug=debug_mode)