import asyncio
import websockets
import json
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

sessions = defaultdict(set)
client_sessions = {}


async def handler(websocket):
    # Try to extract session ID from URL (for BE)
    path = websocket.request.path
    query = urlparse(path).query
    params = parse_qs(query)
    session_id = params.get("session", [None])[0]

    # If not found, wait for Exotel's "connected" and "start" messages
    if not session_id:
        try:
            # Wait for "connected"
            connected_msg = await websocket.recv()
            data = json.loads(connected_msg)
            if data.get("event") != "connected":
                print("error -> Expected 'connected' event")
                return

            # Wait for "start"
            start_msg = await websocket.recv()
            data = json.loads(start_msg)
            if data.get("event") != "start":
                print("error -> Expected 'start' event")
                return
            custom_params = data.get("start", {}).get("custom_parameters", {})
            session_id = custom_params.get("session")
            # print("SESSION ID", session_id)
            if not session_id:
                print("error -> Missing session in custom_parameters")
                return
        except Exception:
            print("error -> Failed to get session ID")
            return

    # Register client in session
    sessions[session_id].add(websocket)
    client_sessions[websocket] = session_id
    print(f"Client joined session: {session_id}")

    try:
        async for message in websocket:
            for conn in sessions[session_id]:
                if conn != websocket:
                    await conn.send(message)
    except websockets.ConnectionClosed:
        print(
            f"Client in session {session_id} disconnected abruptly. Closing all in session."
        )
        # Disconnect all other clients in the same session
        to_close = list(sessions[session_id])
        for conn in to_close:
            try:
                await conn.close()
                print("REMOVED WS CLIENT", session_id)
            except Exception:
                pass  # Ignore errors if already closed
        # Clean up session
        sessions[session_id].clear()
    finally:
        # Remove this websocket from session and client_sessions
        sessions[session_id].discard(websocket)
        if not sessions[session_id]:
            del sessions[session_id]
        if websocket in client_sessions:
            del client_sessions[websocket]
        print(f"Client left session: {session_id}")


async def main():
    host = "0.0.0.0"
    port = 8766
    async with websockets.serve(handler, host, port):
        print(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR ->: {e}")
