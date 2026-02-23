from fastapi import FastAPI, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
import uuid
from collections import defaultdict
from urllib.parse import unquote
from exo import exo_connect

app = FastAPI()

sessions = defaultdict(set)
client_sessions = {}


async def cleanup_session(session_id, disconnected_websocket=None):
    if session_id not in sessions:
        return
    print(f"Cleaning up session: {session_id}")
    clients_to_remove = list(sessions[session_id])
    for conn in clients_to_remove:
        if conn != disconnected_websocket:
            try:
                await conn.close()
                print(f"Forcibly closed client in session: {session_id}")
            except Exception as e:
                print(f"Error closing client: {e}")
        if conn in client_sessions:
            del client_sessions[conn]
    sessions[session_id].clear()
    del sessions[session_id]
    print(f"Session {session_id} completely cleaned up")


@app.websocket("/ws/{session_id}")
async def exo_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session_id = unquote(session_id).strip("\"'")
    sessions[session_id].add(websocket)
    client_sessions[websocket] = session_id
    print(
        f"Client joined session: {session_id} "
        f"(Total clients in session: {len(sessions[session_id])})"
    )
    try:
        while True:
            message = await websocket.receive_text()
            for conn in list(sessions[session_id]):
                if conn != websocket:
                    try:
                        await conn.send_text(message)
                    except Exception:
                        sessions[session_id].discard(conn)
                        if conn in client_sessions:
                            del client_sessions[conn]
                        print(f"Removed disconnected client from session: {session_id}")
    except WebSocketDisconnect:
        print(f"Client in session {session_id} disconnected")
    except Exception as e:
        print(f"Error in session {session_id}: {e}")
    finally:
        print(
            f"Client disconnected from session {session_id}, cleaning up entire session"
        )
        await cleanup_session(session_id, websocket)


@app.get("/exo_ws")
def exo(background_tasks: BackgroundTasks, request: Request):
    uid = uuid.uuid4()
    scheme = "wss" if request.url.scheme == "https" else "ws"
    host = request.headers.get("host")
    wsUrl = f"wss://{host}/ws/{uid}"
    print("WS URL", wsUrl)
    background_tasks.add_task(exo_connect, wsUrl)
    return {"url": wsUrl}


@app.api_route("/pv_ws", methods=["GET", "POST"])
def pv_ws(request: Request):
    scheme = request.url.scheme
    host = request.headers.get("host")
    redirect_url = f"{scheme}://{host}/pv"
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Speak>hello from plivo</Speak>
        <Redirect>{redirect_url}</Redirect>
    </Response>
    """
    return Response(content=xml_data, media_type="application/xml")


@app.api_route("/pv", methods=["GET", "POST"])
def ws(background_tasks: BackgroundTasks, request: Request):
    uid = uuid.uuid4()
    scheme = "wss" if request.url.scheme == "https" else "ws"
    host = request.headers.get("host")
    wsUrl = f"wss://{host}/ws/{uid}"
    print("WS URL", wsUrl)
    # background_tasks.add_task(pv_connect, wsUrl)
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Stream streamTimeout="86400" keepCallAlive="true" bidirectional="true" contentType="audio/x-l16;rate=16000" audioTrack="inbound">
            {wsUrl}
        </Stream>
    </Response>
    """
    return Response(content=xml_data, media_type="application/xml")
