from dotenv import load_dotenv
import os
import asyncpg


load_dotenv()

pasw = os.getenv("PASSWORD_DB")


async def connection_db():
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            database="homework",
           password=pasw
        )
        return conn

    except Exception as error:
        print(f"Connection Error: {error}")
        return None


async def create_table():
    conn =await connection_db()

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id serial primary key,
                title varchar(100),
                capacity int,
                event_date date
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id serial primary key,
                user_id varchar(100),
                event_id int references events(id),
                status VARCHAR(100),
                regtstered_at timestamp dafault current_timestamp
            );
        """)
        print("bot started ✅")

    except Exception as error:
        print(f"Create table Error: {error}")

    finally:
        await conn.close()
