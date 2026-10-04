import asyncio
import json
import time
from collections import defaultdict
from typing import Optional


class WebSocketManager:
    """Manages WebSocket connections for real-time SOC event broadcasting."""

    def __init__(self):
        self.active_connections: set[asyncio.Queue] = set()
        self.event_history: deque = deque(maxlen=500)
        self.subscription_filters: dict[str, set[str]] = defaultdict(set)
        self.broadcast_stats = {
            "total_broadcasts": 0,
            "failed_deliveries": 0,
            "last_broadcast": None,
        }

    async def connect(self, ws) -> None:
        """Accept a new WebSocket connection and register it."""
        queue: asyncio.Queue = asyncio.Queue()
        self.active_connections.add(queue)

        # Send recent history to new connection
        for event in list(self.event_history)[-50:]:
            try:
                await queue.put(event)
            except Exception:
                break

        # Listen for connection close
        try:
            async for message in ws:
                # Handle incoming messages (e.g., subscription requests)
                if message:
                    try:
                        data = json.loads(message)
                        await self._handle_message(queue, data)
                    except (json.JSONDecodeError, Exception):
                        pass
        except Exception:
            pass
        finally:
            self.active_connections.discard(queue)

    def _handle_message(self, queue: asyncio.Queue, data: dict) -> None:
        """Handle incoming WebSocket messages (subscription filters, etc.)."""
        filter_type = data.get("type", "")
        if filter_type == "subscribe":
            event_type = data.get("event_type", "")
            self.subscription_filters[queue].add(event_type)
        elif filter_type == "unsubscribe":
            event_type = data.get("event_type", "")
            self.subscription_filters[queue].discard(event_type)

    async def broadcast(self, event: dict) -> None:
        """Broadcast an event to all active WebSocket connections."""
        self.broadcast_stats["total_broadcasts"] += 1
        self.broadcast_stats["last_broadcast"] = time.time()
        event_with_ts = {**event, "timestamp": time.time()}

        # Add to history
        self.event_history.append(event_with_ts)

        # Notify all connections
        disconnected = set()
        for queue in self.active_connections:
            try:
                # Check if connection subscribes to this event type
                subscribed_types = self.subscription_filters.get(queue, set())
                if not subscribed_types or event.get("type", "") in subscribed_types:
                    await queue.put(event_with_ts)
            except (asyncio.QueueFull, Exception):
                disconnected.add(queue)

        # Remove disconnected
        self.active_connections -= disconnected

        self.broadcast_stats["failed_deliveries"] += len(disconnected)

    async def broadcast_attack(self, attack_data: dict) -> None:
        """Broadcast a new attack detection event."""
        await self.broadcast({
            "type": "new_attack",
            "data": attack_data,
            "source": "detection_engine",
        })

    async def broadcast_incident(self, incident_data: dict) -> None:
        """Broadcast a new incident creation event."""
        await self.broadcast({
            "type": "new_incident",
            "data": incident_data,
            "source": "incident_manager",
        })

    async def broadcast_notification(self, notification: dict) -> None:
        """Broadcast a notification event."""
        await self.broadcast({
            "type": "notification",
            "data": notification,
            "source": "notification_service",
        })

    def get_stats(self) -> dict:
        """Get WebSocket broadcast statistics."""
        return {
            "active_connections": len(self.active_connections),
            "event_history_size": len(self.event_history),
            "total_broadcasts": self.broadcast_stats["total_broadcasts"],
            "failed_deliveries": self.broadcast_stats["failed_deliveries"],
        }


# Global instance for use across the app
ws_manager = WebSocketManager()