import asyncio


async def end_after(seconds, close_session, delete_room):
    """Enforce runtime on the server. Join-token TTL is not a session deadline."""
    await asyncio.sleep(seconds)
    try:
        await asyncio.wait_for(close_session(), timeout=5)
    finally:
        await asyncio.wait_for(delete_room(), timeout=5)
