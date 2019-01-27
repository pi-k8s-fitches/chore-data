#!/usr/bin/env python

import nandy.data
import nandy.store.mysql

nandy.store.mysql.create_database()
data = nandy.data.NandyData()
nandy.store.mysql.Base.metadata.create_all(data.mysql.engine)
data.mysql.session.close()
