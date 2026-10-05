function getWebSocketBaseUrl() {
  const configuredUrl = import.meta.env.VITE_WS_BASE_URL;

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, "");
  }

  const apiUrl = import.meta.env.VITE_API_URL;

  if (apiUrl) {
    return apiUrl
      .replace(/\/api\/v1\/?$/, "")
      .replace(/^https:\/\//, "wss://")
      .replace(/^http:\/\//, "ws://")
      .replace(/\/$/, "");
  }

  const protocol =
    window.location.protocol === "https:" ? "wss" : "ws";

  return `${protocol}://${window.location.host}`;
}

function parseMessage(event) {
  if (typeof event.data !== "string") {
    return null;
  }

  try {
    return JSON.parse(event.data);
  } catch {
    return null;
  }
}

export function connectAttackSocket({
  onMessage,
  onOpen,
  onClose,
  onError,
} = {}) {
  let socket = null;
  let reconnectTimer = null;
  let manuallyClosed = false;
  let reconnectAttempt = 0;

  const url = `${getWebSocketBaseUrl()}/ws/attacks`;

  function clearReconnectTimer() {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  function scheduleReconnect() {
    if (manuallyClosed || reconnectTimer !== null) {
      return;
    }

    reconnectAttempt += 1;

    const delay = Math.min(
      1000 * 2 ** Math.min(reconnectAttempt - 1, 4),
      15000
    );

    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  }

  function connect() {
    if (manuallyClosed) {
      return;
    }

    clearReconnectTimer();

    try {
      socket = new WebSocket(url);
    } catch (error) {
      onError?.(error);
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      reconnectAttempt = 0;
      onOpen?.();

      try {
        socket?.send("ping");
      } catch {
        // Ignore socket teardown errors.
      }
    };

    socket.onmessage = (event) => {
      const message = parseMessage(event);

      if (message) {
        onMessage?.(message);
      }
    };

    socket.onerror = (error) => {
      onError?.(error);
    };

    socket.onclose = (event) => {
      socket = null;
      onClose?.(event);
      scheduleReconnect();
    };
  }

  manuallyClosed = false;
  connect();

  return () => {
    manuallyClosed = true;
    clearReconnectTimer();

    if (socket) {
      try {
        socket.close();
      } catch {
        // Ignore close errors.
      }
    }

    socket = null;
  };
}

export function getWebSocketBaseUrlForDebugging() {
  return getWebSocketBaseUrl();
}