# warbler

1. Can a table have two foreign keys to the same table?
    - A table may have multiple foreign keys and each FK can have different parent table. Each FK is enforced independently by the database system.
    - Cascading relationships between tables can be established using FKs.

2. How is the logged user being kept track of?
    - If there is any user logged in/session, that user/key will be add to flask gobal

3. What is Flask's g object?
    - Global namespace for holding any data I want during a simple app context.

4. What is the purpose of add_user_to_g?
    - If there is any current user in session, g.user will get the data from the actual user that is logged in/session and will add it to flask.

5. What does @app.before_request mean?
    - create a function that will run before each request. It useful to load a user from the current session and work with g object. 