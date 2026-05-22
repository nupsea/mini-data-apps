import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import duckdb
    import datetime

    return datetime, duckdb, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Twitter Model
    This interactive SQL notebook implements the classic Twitter-like schema from **Designing Data-Intensive Applications**

    We represent the core social graph and activity stream using three relational tables in **DuckDB**:
    1. **`users`**: The profiles of users on the network.
    2. **`posts`**: The tweets sent by users.
    3. **`follows`**: The directed follow relationships between users.
    """)
    return


@app.cell
def _(mo):
    ## Relational schema design.

    mo.mermaid(
        """
        erDiagram
            users ||--o{ posts : "posts (sender_id)"
            users ||--o{ follows : "follower (follower_id)"
            users ||--o{ follows : "followee (followee_id)"

            users {
                varchar id PK
                varchar username UK
                varchar name
            }
            posts {
                varchar id PK
                varchar sender_id FK
                varchar content
                timestamp timestamp
            }
            follows {
                varchar follower_id PK, FK
                varchar followee_id PK, FK
            }
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Process

    1. Create the schematic tables
    2. Insert data into the tables
    3. View the data tables
    4. Join the tables to obtain the tweets for a particular user
    """)
    return


@app.cell
def _(duckdb):
    # Drop existing tables to ensure the cell is idempotent
    duckdb.execute("DROP TABLE IF EXISTS follows;")
    duckdb.execute("DROP TABLE IF EXISTS posts;")
    duckdb.execute("DROP TABLE IF EXISTS users;")

    # 1. Create users table
    duckdb.execute("""
    CREATE TABLE users (
        id VARCHAR PRIMARY KEY,
        username VARCHAR NOT NULL UNIQUE,
        name VARCHAR NOT NULL
    );
    """)

    # 2. Create posts table
    duckdb.execute("""
    CREATE TABLE posts (
        id VARCHAR PRIMARY KEY,
        sender_id VARCHAR NOT NULL REFERENCES users(id),
        content VARCHAR NOT NULL,
        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Create follows table
    duckdb.execute("""
    CREATE TABLE follows (
        follower_id VARCHAR NOT NULL REFERENCES users(id),
        followee_id VARCHAR NOT NULL REFERENCES users(id),
        PRIMARY KEY (follower_id, followee_id)
    );
    """)

    # Verify they exist
    print(duckdb.execute("SHOW TABLES;").fetchall())
    return


@app.cell
def _(duckdb):
    # Insert sample users (including 'duckdb', which is the default active session user)
    users_data = [
        ('duckdb', '@duckdb', 'Default SQL Session User'),
        ('alice', '@alice', 'Alice Vance'),
        ('bob', '@bob', 'Bob Builder'),
        ('charlie', '@charlie', 'Charlie Bucket'),
        ('diana', '@diana', 'Diana Prince'),
        ('elon', '@elon', 'Elon Musketeer'),
        ('neo', '@neo', 'John Anderson'),
        ('batman', '@batman', 'Bruce Wayne')
    ]

    for uid, uname, name in users_data:
        duckdb.execute("INSERT INTO users VALUES (?, ?, ?);", [uid, uname, name])
    return


@app.cell
def _(duckdb):
    # Insert sample follow relationships
    # 'duckdb' follows alice, bob, and charlie
    follows_data = [
        ('duckdb', 'alice'),
        ('duckdb', 'bob'),
        ('duckdb', 'charlie'),
        ('alice', 'bob'),
        ('alice', 'diana'),
        ('bob', 'alice'),
        ('charlie', 'alice'),
        ('charlie', 'diana'),
        ('charlie', 'batman'),
        ('diana', 'elon'),
        ('diana', 'neo'),
        ('diana', 'batman'),
        ('neo', 'batman'),
        ('neo', 'diana')
    ]
    for follower, followee in follows_data:
        duckdb.execute("INSERT INTO follows VALUES (?, ?);", [follower, followee])
    return


@app.cell
def _(datetime, duckdb):
    # Insert sample posts with realistic relative timestamps
    now = datetime.datetime.now()

    posts_data = [
        ('p1', 'neo', 'Building a new mini data app using DuckDB and Marimo!', now - datetime.timedelta(minutes=5)),
        ('p2', 'alice', 'Good morning world! Coffee and code is all I need today', now - datetime.timedelta(minutes=15)),
        ('p3', 'charlie', 'Just found a golden ticket in my database query!', now - datetime.timedelta(hours=1)),
        ('p4', 'diana', 'Sleek layouts, custom CSS, and zero framework overhead. Pure gold.', now - datetime.timedelta(hours=2)),
        ('p5', 'elon', 'To the moon and back! ', now - datetime.timedelta(hours=4)),
        ('p6', 'neo', 'Who is up for some pair programming later? ', now - datetime.timedelta(hours=6)),
        ('p7', 'alice', 'DuckDB is incredibly fast. Highly recommend checking it out.', now - datetime.timedelta(hours=12)),
        ('p8', 'charlie', 'Working on a new feature for the SQL editor! ', now - datetime.timedelta(days=1)),
        ('p9', 'diana', 'Just finished designing the home timeline query!', now - datetime.timedelta(days=2)),
        ('p10', 'batman', 'The caped crusader is back in black!', now - datetime.timedelta(minutes=1))
    ]

    for pid, sender, content, ts in posts_data:
        duckdb.execute("INSERT INTO posts VALUES (?, ?, ?, ?);", [pid, sender, content, ts])
    return


@app.cell
def _(duckdb, follows, mo, posts, users):

    # 1. Fetch raw tables directly as Polars DataFrames using .pl()
    users_raw = duckdb.execute("SELECT * FROM users").pl()
    follows_raw = duckdb.execute("SELECT * FROM follows").pl()
    posts_raw = duckdb.execute("SELECT * FROM posts").pl()

    # 2. Render interactive tabs (marimo automatically handles the Polars schema)
    raw_tables_tabs = mo.ui.tabs({
        "Users Table": mo.ui.table(users_raw, label="Registered Users"),
        "Follows Table": mo.ui.table(follows_raw, label="Following Relationships"),
        "Posts Table": mo.ui.table(posts_raw, label="All Posted Tweets")
    })

    mo.md(
        f"""
        ### 🔍 Inspect Raw Database Tables
        Click through the tabs below to verify the tables and check the schema records:

        {raw_tables_tabs}
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In DuckDB, the keyword current_user evaluates to the active database user ('duckdb'). Since we have created a user in our users table with the ID 'duckdb', and configured them to follow @alice, @bob, and @charlie, this query compiles and runs unmodified in our database context!
    """)
    return


@app.cell
def _(follows, mo, posts, users):
    _df = mo.sql(
        f"""
        SELECT posts.*, users.* FROM posts
          JOIN follows ON posts.sender_id = follows.followee_id
          JOIN users   ON posts.sender_id = users.id
          WHERE follows.follower_id = current_user
          ORDER BY posts.timestamp DESC
          LIMIT 1000
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    > This fetches the tweets the user 'duckdb' is interested in.
    """)
    return


if __name__ == "__main__":
    app.run()
