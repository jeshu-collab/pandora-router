import asyncio
import websockets
import json
import os
from datetime import datetime

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] NODE JOINED. ACTIVE: {len(connected_clients)}")
    try:
        async for message in websocket:
            # Broadcast to all other connected nodes (Dashboard or AI)
            if connected_clients:
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients if client != websocket],
                    return_exceptions=True
                )
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[-] NODE LEFT. ACTIVE: {len(connected_clients)}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🟢 PANDORA ROUTER ONLINE [PORT {port}]")
    async with websockets.serve(handler, "0.0.0.0", port, max_size=10**7):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
