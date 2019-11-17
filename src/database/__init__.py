from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import discord_logging
from shutil import copyfile

Base = declarative_base()

import static
import utils
from ._keystore import _DatabaseKeystore
from ._reminders import _DatabaseReminders
from ._comments import _DatabaseComments
from ._subreddits import _DatabaseSubreddit
from ._users import _DatabaseUsers

log = discord_logging.get_logger()


class Database(_DatabaseReminders, _DatabaseComments, _DatabaseKeystore, _DatabaseSubreddit, _DatabaseUsers):
	def __init__(self, debug=False, publish=False):
		log.info(f"Initializing database class: debug={debug} publish={publish}")
		self.debug = debug
		self.engine = None
		self.init(debug, publish)

		_DatabaseReminders.__init__(self)
		_DatabaseComments.__init__(self)
		_DatabaseKeystore.__init__(self)
		_DatabaseSubreddit.__init__(self)
		_DatabaseUsers.__init__(self)

	def init(self, debug, publish):
		if debug:
			self.engine = create_engine(f'sqlite:///:memory:')
		else:
			self.engine = create_engine(f'sqlite:///{static.DATABASE_NAME}')

		Session = sessionmaker(bind=self.engine)
		self.session = Session()

		if publish:
			Base.metadata.drop_all(self.engine)

		Base.metadata.create_all(self.engine)

		if self.get_keystore("remindme_comment") is None:
			self.save_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

		self.commit()

	def backup(self):
		log.info("Backing up database")
		self.commit()
		self.close()

		if not os.path.exists(static.BACKUP_FOLDER_NAME):
			os.makedirs(static.BACKUP_FOLDER_NAME)

		copyfile(
			static.DATABASE_NAME,
			static.BACKUP_FOLDER_NAME + "/" + utils.datetime_now().strftime("%Y-%m-%d_%H-%M") + ".db")

		self.init(self.debug, False)

	def commit(self):
		self.session.commit()

	def close(self):
		self.engine.dispose()
