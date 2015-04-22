import gdb

import pymongo

import mongoengine

# NOTE: The read_preference should not be needed.  This is a workaround for a
# bug in pymongo.  (http://goo.gl/Somoeu)
mongoengine.connect('memoryoracle',
                    read_preference=\
                            pymongo.read_preferences.ReadPreference.PRIMARY)
