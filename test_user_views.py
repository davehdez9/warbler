"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client and sample data"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="david",
                                    email="user1@gm.com",
                                    password="password",
                                    image_url=None)
        
        self.testuser_id = 987
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("daisy", "test1@gm.com", "password", None)
        self.u1_id = 234
        self.u1.id = self.u1_id

        self.u2 = User.signup("luz", "test2@gm.com", "password", None)
        self.u2_id = 2334
        self.u2.id = self.u2_id

        self.u3 = User.signup("nelson", "test3@gm.com", "password", None)
        self.u4 = User.signup("miguel", "test4@gm.com", "password", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("david", str(resp.data))
            self.assertIn("daisy", str(resp.data))
            self.assertIn("luz", str(resp.data))
            self.assertIn("nelson", str(resp.data))
            self.assertIn("miguel", str(resp.data))

    def test_user_search(self):
        with self.client as c:
            resp = c.get("/users?q=da")

            self.assertIn("david", str(resp.data))
            self.assertIn("daisy", str(resp.data))
            

            self.assertNotIn("luz", str(resp.data))
            self.assertNotIn("nelson", str(resp.data))
            self.assertNotIn("miguel", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("david", str(resp.data))

    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating pizza", user_id=self.testuser_id)
        m3 = Message(id=412, text="other message", user_id=self.u1_id)
        db.session.add_all([m1,m2,m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=412)

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("david", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # Test for a count of 2 messages
            self.assertIn("2", found[0].text)

            # Test for a count of 0 followers
            self.assertIn("0", found[1].text)

            # Test for a count of 0 following
            self.assertIn("0", found[2].text)

            # Test for a count of 1 like 
            self.assertIn("1",found[3].text)

    def test_to_add_likes(self):
        m = Message(id=1900, text="I am going to vote", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/messages/1900/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1900).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="other message").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==m.id
        ).one()

        # Now we are sure that testuser likes message "other message"
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # The likes has been delete
            self.assertEqual(len(likes), 0)

    def test_unauthenticate_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="other message").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized.", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):
        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("david", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # test for a count of 2 following 
            self.assertIn("2", found[1].text)

            # test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # test a count of 0 likes
            self.assertIn("0", found[3].text)

    def test_show_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("daisy", str(resp.data))
            self.assertIn("luz", str(resp.data))
            self.assertNotIn("nelson", str(resp.data))
            self.assertNotIn("miguel", str(resp.data))

    def test_show_followers(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("daisy", str(resp.data))
            self.assertNotIn("luz", str(resp.data))
            self.assertNotIn("nelson", str(resp.data))
            self.assertNotIn("miguel", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("daisy", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("daisy", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    






