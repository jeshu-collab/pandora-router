import asyncio
import websockets
import json
import os
from aiohttp import web

# --- MEMORY STORAGE ---
connected_clients = set()
current_task = {"url": ""}  # Stores the camera URL set by users

# --- 1. WEBSOCKET HANDLER (For Dashboard) ---
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] NODE JOINED. ACTIVE: {len(connected_clients)}")
    try:
        async for message in websocket:
            # If dashboard sends a START command, update the task URL
            data = json.loads(message)
            if data.get("command") == "START":
                current_task["url"] = data.get("url")
                print(f"[*] Task Updated: {current_task['url']}")

            # Broadcast message to everyone else
            if connected_clients:
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients if client != websocket],
                    return_exceptions=True
                )
    except Exception:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[-] NODE LEFT. ACTIVE: {len(connected_clients)}")

# --- 2. HTTP ROUTES (For Hugging Face AI Polling) ---
async def get_task(request):
    """AI Node calls this to ask: What should I watch?"""
    return web.json_response(current_task)

async def push_alert(request):
    """AI Node calls this to send a snapshot"""
    data = await request.json()
    # Relay the alert to all WebSocket clients (the Dashboard)
    message = json.dumps(data)
    for client in connected_clients:
        await client.send(message)
    print("🚨 Alert pushed to Dashboard")
    return web.Response(text="OK")

# --- 3. SERVER STARTUP ---
async def main():
    port = int(os.environ.get("PORT", 8765))
    
    # Setup HTTP Server
    app = web.Application()
    app.router.add_get('/get-task', get_task)
    app.router.add_post('/push-alert', push_alert)
    
    # Setup WebSocket Server
    ws_server = websockets.serve(ws_handler, "0.0.0.0", port, max_size=10**7)

    print(f"🟢 PANDORA HYBRID ROUTER ONLINE [PORT {port}]")
    
    # Run both HTTP and WS together
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080) # HTTP on 8080 or same port if configured
    
    await asyncio.gather(ws_server, site.start())
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
