export function getSocEvent(message) {
  if (!message || typeof message !== "object") {
    return null;
  }

  return {
    event:
      message.event ||
      message.type ||
      message.name ||
      "unknown",
    data:
      message.data ||
      message.payload ||
      message.item ||
      message.attack ||
      null,
    timestamp: message.timestamp || null,
  };
}

export function getEventData(message, eventName) {
  const event = getSocEvent(message);

  if (!event || event.event !== eventName) {
    return null;
  }

  return event.data;
}