from connection import connection_db

async def add_event_db(title: str, capacity: int, event_date: str):
    """Илова кардани чорабинии нав"""
    conn = await connection_db()
    if not conn:
        return
    try:
        await conn.execute(
            "INSERT INTO events (title, capacity, event_date) VALUES ($1, $2, $3)",
            title, capacity, event_date
        )
    finally:
        await conn.close()

async def get_all_events_db():
    """Гирифтани ҳамаи чорабиниҳо"""
    conn = await connection_db()
    if not conn:
        return []
    try:
        rows = await conn.fetch("SELECT id, title, capacity, event_date FROM events ORDER BY id")
        return rows
    finally:
        await conn.close()

async def get_event_db(event_id: int):
    """Гирифтани як чорабинӣ аз рӯи ID"""
    conn = await connection_db()
    if not conn:
        return None
    try:
        row = await conn.fetchrow("SELECT id, title, capacity, event_date FROM events WHERE id = $1", event_id)
        return row
    finally:
        await conn.close()

async def get_user_registration_db(user_id: str, event_id: int):
    """Санҷидани он ки оё корбар аллакай сабт шудааст ё не"""
    conn = await connection_db()
    if not conn:
        return None
    try:
        row = await conn.fetchrow(
            "SELECT id, status FROM registrations WHERE user_id = $1 AND event_id = $2",
            str(user_id), event_id
        )
        return row
    finally:
        await conn.close()

async def get_confirmed_count_db(event_id: int):
    """Шумораи ҷойҳои тасдиқшуда"""
    conn = await connection_db()
    if not conn:
        return 0
    try:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM registrations WHERE event_id = $1 AND status = 'confirmed'",
            event_id
        )
        return count
    finally:
        await conn.close()

async def register_user_db(user_id: str, event_id: int):
    """Сабти номи корбар (confirmed ё waitlist)"""
    conn = await connection_db()
    if not conn:
        return "error"
    try:
        event = await get_event_db(event_id)
        if not event:
            return "not_found"
            
        capacity = event["capacity"]
        confirmed_count = await get_confirmed_count_db(event_id)
        
        status = "confirmed" if confirmed_count < capacity else "waitlist"
        
        await conn.execute(
            "INSERT INTO registrations (user_id, event_id, status) VALUES ($1, $2, $3)",
            str(user_id), event_id, status
        )
        return status
    finally:
        await conn.close()

async def cancel_registration_db(user_id: str, event_id: int):
    """Бекор кардани сабти ном ва ба таври автоматӣ гузаронидани шахси якуми waitlist"""
    conn = await connection_db()
    if not conn:
        return None, None
    try:
        reg = await get_user_registration_db(user_id, event_id)
        if not reg:
            return None, None
            
        reg_id, old_status = reg["id"], reg["status"]
        
        # Нест кардани сабти корбар
        await conn.execute("DELETE FROM registrations WHERE id = $1", reg_id)
        
        promoted_user_id = None
        
        # Агар шахси бекоркардашуда confirmed буд, навбати интизориро месанҷем
        if old_status == "confirmed":
            waitlist_user = await conn.fetchrow(
                "SELECT id, user_id FROM registrations WHERE event_id = $1 AND status = 'waitlist' ORDER BY registered_at ASC LIMIT 1",
                event_id
            )
            if waitlist_user:
                waitlist_reg_id = waitlist_user["id"]
                promoted_user_id = waitlist_user["user_id"]
                
                # Гузаронидани ҳолат ба confirmed
                await conn.execute("UPDATE registrations SET status = 'confirmed' WHERE id = $1", waitlist_reg_id)
                
        return old_status, promoted_user_id
    finally:
        await conn.close()

async def get_user_events_db(user_id: str):
    """Гирифтани рӯйхати чорабиниҳои корбар"""
    conn = await connection_db()
    if not conn:
        return []
    try:
        rows = await conn.fetch("""
            SELECT e.title, e.event_date, r.status, e.id 
            FROM registrations r
            JOIN events e ON r.event_id = e.id
            WHERE r.user_id = $1
        """, str(user_id))
        return rows
    finally:
        await conn.close()