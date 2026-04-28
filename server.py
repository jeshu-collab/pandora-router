import asyncio
import os
import json
from aiohttp import web
import websockets
from websockets.asyncio.server import serve

# --- DATA STORAGE ---
connected_clients = set()
current_task = {"url": ""}

# --- HTTP HANDLERS ---
async def get_task(request):
    return web.json_response(current_task)

async def push_alert(request):
    try:
        data = await request.json()
        message = json.dumps(data)
        # Broadcast the alert to all connected Dashboards
        if connected_clients:
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        return web.Response(text="Alert Sent")
    except Exception as e:
        return web.Response(text=str(e), status=400)

# --- WEBSOCKET HANDLER ---
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] Dashboard Linked. Total: {len(connected_clients)}")
    try:
        async for message in websocket:
            data = json.loads(message)
            # When user clicks 'Initialize' on Dashboard
            if data.get("command") == "START":
                current_task["url"] = data.get("url")
                print(f"[*] New Task Set: {current_task['url']}")
            
            # General broadcast
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
    except Exception:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[-] Dashboard Unlinked. Total: {len(connected_clients)}")

# --- STARTUP ---
async def main():
    port = int(os.environ.get("PORT", 8765))
    
    # 1. Setup the HTTP App
    app = web.Application()
    app.router.add_get('/get-task', get_task)
    app.router.add_post('/push-alert', push_alert)
    
    # 2. Start HTTP Server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # 3. Start WebSocket Server on the SAME port is tricky on Render, 
    # so we usually run them on the same event loop.
    # Note: Render works best if you use a library like 'aiohttp' for BOTH.
    # For now, let's keep it simple: 
    async with serve(ws_handler, "0.0.0.0", 8765): # Use a different internal port
        print(f"🟢 PANDORA HYBRID ROUTER LIVE")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
