"""Progress Tracker Service - Real-time progress events for learning path generation."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator


@dataclass
class ProgressEvent:
    """A progress event for streaming to the client."""

    type: str  # "progress" | "complete" | "error"
    phase: str  # "profiling" | "curriculum" | "scheduling" | "resources" | "assessments"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "phase": self.phase,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp
        }


class ProgressTracker:
    """
    Async progress tracker using asyncio.Queue.

    Thread-safe for concurrent event emission from multiple agents.
    """

    def __init__(self, max_size: int = 100):
        """Initialize the tracker with an async queue."""
        self._queue: asyncio.Queue[ProgressEvent] = asyncio.Queue(maxsize=max_size)
        self._active = True

    async def emit(self, event: ProgressEvent) -> None:
        """
        Emit a progress event to the queue.

        Non-blocking if queue is not full. If queue is full, oldest events
        may be dropped (though with max_size=100, this is unlikely).
        """
        if self._active:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest event and add new one
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(event)
                except asyncio.QueueEmpty:
                    pass

    async def emit_progress(
        self,
        phase: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Convenience method to emit a progress event."""
        await self.emit(ProgressEvent(
            type="progress",
            phase=phase,
            message=message,
            data=data
        ))

    async def emit_complete(
        self,
        message: str = "Complete",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a completion event."""
        await self.emit(ProgressEvent(
            type="complete",
            phase="complete",
            message=message,
            data=data
        ))

    async def emit_error(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit an error event."""
        await self.emit(ProgressEvent(
            type="error",
            phase="error",
            message=message,
            data=data
        ))

    async def stream(self) -> AsyncGenerator[ProgressEvent, None]:
        """
        Async generator that yields events as they arrive.

        Yields events until a 'complete' or 'error' event is received,
        or until the tracker is closed.
        """
        while self._active:
            try:
                # Wait for event with timeout to allow checking _active flag
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                yield event

                # Stop streaming on complete or error
                if event.type in ("complete", "error"):
                    break

            except asyncio.TimeoutError:
                # Continue waiting if still active
                continue

    def close(self) -> None:
        """Close the tracker and stop streaming."""
        self._active = False


def create_progress_tracker() -> ProgressTracker:
    """Factory function to create a new progress tracker instance."""
    return ProgressTracker()
