import os
import json
import asyncio
from aiohttp import web, WSMsgType

# --- DATA STORAGE ---
connected_clients = set()
current_task = {"url": ""}

# --- 1. HTTP HANDLERS ---
async def get_task(request):
    return web.json_response(current_task)

async def push_alert(request):
    try:
        data = await request.json()
        # Broadcast to all connected WebSockets
        for ws in connected_clients:
            await ws.send_json(data)
        return web.Response(text="Alert Sent")
    except Exception as e:
        return web.Response(text=str(e), status=400)

# --- 2. WEBSOCKET HANDLER ---
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_clients.add(ws)
    print(f"[+] Dashboard Linked. Total: {len(connected_clients)}")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                # When user sets a new camera URL
                if data.get("command") == "START":
                    current_task["url"] = data.get("url")
                    print(f"[*] New Task Set: {current_task['url']}")
                
                # Broadcast message to other dashboards
                for client in connected_clients:
                    if client != ws:
                        await client.send_str(msg.data)
    finally:
        connected_clients.remove(ws)
        print(f"[-] Dashboard Unlinked. Total: {len(connected_clients)}")
    return ws

# --- 3. STARTUP ---
async def main():
    app = web.Application()
    
    # Standard HTTP routes
    app.router.add_get('/get-task', get_task)
    app.router.add_post('/push-alert', push_alert)
    
    # WebSocket route (Users connect to wss://your-app.onrender.com/ws)
    app.router.add_get('/ws', ws_handler)

    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    print(f"🟢 PANDORA HYBRID ROUTER LIVE ON PORT {port}")
    await site.start()
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
