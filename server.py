import asyncio
import websockets
import json
import os
from datetime import datetime

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] NODE JOINED. TOTAL: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            stamp = datetime.now().strftime("%H:%M:%S")

            if "alert_type" in data:
                print(f"[{stamp}] 🚨 ALERT: {data['alert_type']}")
            elif "command" in data:
                print(f"[{stamp}] ⚙️ COMMAND: {data['command']}")

            # Robust Broadcast
            if connected_clients:
                # We use send() in a way that doesn't crash if one client is slow
                tasks = [asyncio.create_task(client.send(message)) 
                         for client in connected_clients if client != websocket]
                if tasks:
                    await asyncio.wait(tasks)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[-] NODE LEFT. TOTAL: {len(connected_clients)}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🟢 PANDORA ROUTER ONLINE [PORT {port}]")
    async with websockets.serve(handler, "0.0.0.0", port, max_size=10**7):
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
