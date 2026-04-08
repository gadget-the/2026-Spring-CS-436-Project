import sys
import os
import json
import base64
from socket import socket, AF_INET, SOCK_DGRAM

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

class socket_client():
    def __init__(self, host='localhost', port=12000):
        self.serverAddr = (host, port)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(5.0)
        self.username = ""

    def talk(self, payload):
        self.sock.sendto(json.dumps(payload).encode(), self.serverAddr)
        data, _ = self.sock.recvfrom(65536)
        return json.loads(data.decode())

    def run(self):
        print("--- RPG GAME LOGIN ---")
        while True:
            self.username = input("Enter username: ")
            password = input("Enter password: ")
            try:
                res = self.talk({"action": "LOGIN", "username": self.username, "password": password})
                if res['status'] == "success":
                    state = res['state']
                    break
                print("Login rejected.")
                if input("1. Try again\n2. Quit\nChoice: ") == '2': return
            except:
                print("Server not responding.")
                return

        if state.get('lives', 0) <= 0:
            print("GAME OVER for this warrior.")
            return

        # Avatar Upload
        if input("\nDo you want to upload an avatar file? (y/n): ").lower() == 'y':
            fname = input("Enter image filename (e.g. B.jpg): ")
            fpath = os.path.join(ROOT_DIR, fname)
            alt_fpath = os.path.join(ROOT_DIR, "Avatars", fname)
            
            target_path = fpath if os.path.exists(fpath) else alt_fpath if os.path.exists(alt_fpath) else None

            if target_path:
                with open(target_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                self.talk({"action": "UPLOAD_AVATAR", "username": self.username, "file_data": encoded})
                print("Avatar uploaded.")
            else:
                print(f"ERROR: Could not find '{fname}'.")

        # Stats Assignment
        if state.get('sword_strength') == -1:
            print("\nYou are given 10 strengths.")
            while True:
                try:
                    s = [int(input(f"Assign {x} [0-3]: ")) for x in ["Sword", "Shield", "Slaying", "Healing"]]
                    if sum(s) == 10 and all(0 <= x <= 3 for x in s):
                        self.talk({"action": "SET_STATS", "username": self.username, "stats": s})
                        print("Stats saved.")
                        break
                    print("Invalid! Sum must be 10 and max strength is 3.")
                except ValueError: print("Enter numbers only.")

        # Prompt active users
        if input("\nDo you want to see a list of other active warriors? (y/n): ").lower() == 'y':
            res = self.talk({"action": "GET_ACTIVE", "username": self.username})
            others = [n for n in res.get('users', {}).keys() if n != self.username]
            if not others:
                print("No other active user exists yet.")
            else:
                print(f"Active Warriors: {', '.join(others)}")

        # Download Avatar
        if input("\nDo you want to download an active warrior's avatar file? (y/n): ").lower() == 'y':
            target = input("Enter the username (or number) of the other active warrior: ")
            res = self.talk({"action": "DOWNLOAD_AVATAR", "username": self.username, "target": target})
            if res.get("status") == "success":
                save_path = os.path.join(ROOT_DIR, f"downloaded_{target}.jpg")
                with open(save_path, "wb") as f:
                    f.write(base64.b64decode(res["file_data"]))
                print(f"SUCCESS: Avatar saved to {save_path}")
            else:
                print("Failed to download avatar.")

        # Ask fight
        if input("\nDo you want the server to send the list of confirmed fight requests? (y/n): ").lower() == 'y':
            res = self.talk({"action": "GET_FIGHTS", "username": self.username})
            fights = res.get("fights", [])
            if not fights:
                print("Empty response.")
            else:
                print("\n| Requester | Boss | Item | Strength | Winner |")
                print("-" * 55)
                for f in fights:
                    print(f"| {f['requester']:<9} | {f['boss']:<4} | {f['item']:<4} | {f['strength']:<8} | {f['winner']:<6} |")

        # Fight Loop
        while True:
            if input("\nDo you want to send a fight request? (y/n): ").lower() != 'y':
                break
            target = input("Enter target warrior username: ")
            item = input("Enter fighting item (sword/slaying-potion): ").lower()
            strength = input("Enter strength: ")
            res = self.talk({"action": "FIGHT", "username": self.username, "target": target, "item": item, "strength": strength})
            if res.get("status") == "success":
                print("Fight processed successfully!")
            else:
                print("Fight rejected.")
            
            if input("Do you want to send a NEW fight request? (y/n): ").lower() != 'y':
                break

        # Final Active Users
        if input("\nDo you want to get a list of active users and their current states? (y/n): ").lower() == 'y':
            res = self.talk({"action": "GET_ACTIVE", "username": self.username})
            print("\n{:<10} | {:<5} | {:<6} | {:<10} | {:<10} | {:<5}".format("User", "Sword", "Shield", "Slay", "Heal", "Lives"))
            print("-" * 65)
            for name, s in res['users'].items():
                print(f"{name:<10} | {s['sword_strength']:<5} | {s['shield_strength']:<6} | {s['slaying_potion_strength']:<10} | {s['healing_potion_strength']:<10} | {s['lives']:<5}")
        
        print("\nClient program quitting.")

if __name__ == "__main__":
    client = socket_client()
    client.run()