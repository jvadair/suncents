import sqlalchemy as db
from pyntree import Node
from time import sleep

config = Node('config.yml')

# DB config
dbsettings = config.db
while True:
    try:
        engine = db.create_engine(url="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(  # me:password@host:port/db
                dbsettings.user(), dbsettings.password(), dbsettings.host(), dbsettings.port(), dbsettings.database()
            ),
            pool_pre_ping=True
        )
        metadata = db.MetaData()
        conn = engine.connect()
        print("Database connection established!")
        break
    except Exception as e:
        print(e)
        print("Database connection failed, re-attemting in 30 seconds...")
        sleep(30)
