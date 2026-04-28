import asyncio
import websockets
import json
import os
from datetime import datetime

# Global set of connected clients (AI Nodes and Dashboards)
connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] NODE JOINED. ACTIVE CONNECTIONS: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            stamp = datetime.now().strftime("%H:%M:%S")

            # LOGGING LOGIC
            if "alert_type" in data:
                print(f"[{stamp}] 🚨 ALERT: {data['alert_type']} at {data['building']}")
            elif "command" in data:
                print(f"[{stamp}] ⚙️ COMMAND: {data['command']} -> {data.get('url', 'USB')}")

            # BROADCAST ENGINE: Forward message to everyone else
            if connected_clients:
                await asyncio.wait([client.send(message) for client in connected_clients if client != websocket])

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[-] NODE LEFT. ACTIVE CONNECTIONS: {len(connected_clients)}")

async def main():
    # Render/Railway assign a port via environment variable
    port = int(os.environ.get("PORT", 8765))
    print(f"🟢 PANDORA ROUTER ONLINE [PORT {port}]")
    
    async with websockets.serve(handler, "0.0.0.0", port, max_size=10**7):
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())