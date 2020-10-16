"""Message Model Test"""

# run the test like:
#     python -m unittest test_message_model.py

import os 
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    
    def setUp(self):
        """Create test client, add sample data"""
        db.drop_all()
        db.create_all()

        self.uid = 1234
        u = User.signup("test1", "test1@test.com", "test1", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model works?"""

        m = Message(
            text ="a Tweet",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        # User should have 1 Message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "a Tweet")

    def test_messages_likes(self):
        m1 = Message(
            text ="Another Tweet",
            user_id=self.uid
        )

        m2 = Message(
            text="One more test",
            user_id=self.uid
        )

        u = User.signup("boringtest", "test@test.com", "test", None)
        uid = 123
        u.id = uid
        db.session.add_all([m1,m2, u])
        db.session.commit()

        u.likes.append(m1)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)







