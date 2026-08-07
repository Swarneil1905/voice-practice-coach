import asyncio
import unittest
from unittest.mock import AsyncMock
from session_limit import end_after


class DeadlineTests(unittest.IsolatedAsyncioTestCase):
    async def test_closes_session_and_room(self):
        close, delete = AsyncMock(), AsyncMock()
        await end_after(0, close, delete)
        close.assert_awaited_once()
        delete.assert_awaited_once()

    async def test_deletes_room_even_when_close_fails(self):
        close, delete = AsyncMock(side_effect=RuntimeError("closed")), AsyncMock()
        with self.assertRaises(RuntimeError):
            await end_after(0, close, delete)
        delete.assert_awaited_once()

    async def test_cancelled_deadline_does_not_delete_early(self):
        close, delete = AsyncMock(), AsyncMock()
        task = asyncio.create_task(end_after(480, close, delete))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        delete.assert_not_awaited()
