from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# render_as_batch: SQLite (dev) tidak mendukung ALTER kolom secara langsung.
migrate = Migrate(render_as_batch=True)
