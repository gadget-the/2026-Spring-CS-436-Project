import sys
import os
import json
import base64
from socket import socket, AF_INET, SOCK_DGRAM

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from warrior_class import warrior

class socket_server():
    def __init__(self, port=12000):
        self.serverPort = port
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        
        # Users: A, B, C, D
        self.users = {name: warrior(name, name) for name in ["A", "B", "C", "D"]}
        for name, u in self.users.items():
            u.lives = 2 
            
        self.confirmed_fights = []

    def start(self):
        self.serverSocket.bind(('', self.serverPort))
        print(f"The server is ready to receive on port {self.serverPort}")

        while True:
            try:
                message, clientAddress = self.serverSocket.recvfrom(65536)
                data = json.loads(message.decode())
                action = data.get("action")
                username = data.get("username", "Unknown")
                
                print(f"Received a {action} request from user {username}")
                
                response = self.handle_logic(action, data)
                self.serverSocket.sendto(json.dumps(response).encode(), clientAddress)
                print(f"Handled {action} for {username}")
            except Exception as e:
                print(f"Server Error: {e}")

    def print_fancy_table(self):
        print("\n" + "="*70)
        print("{:<12} | {:<7} | {:<8} | {:<10} | {:<10} | {:<5}".format(
            "Active user", "Sword", "Shield", "Slay-Pot", "Heal-Pot", "Lives"))
        print("-" * 70)
        
        active_count = 0
        for name, u in self.users.items():
            if u.lives > 0 and u.sword_strength != -1:
                print("{:<12} | {:<7} | {:<8} | {:<10} | {:<10} | {:<5}".format(
                    name, u.sword_strength, u.shield_strength, 
                    u.slaying_potion_strength, u.healing_potion_strength, u.lives))
                active_count += 1
                
        if active_count == 0:
            print("{:<70}".format("No active users yet."))
        print("="*70 + "\n")

    def handle_logic(self, action, data):
        username = data.get("username")
        user = self.users.get(username)
        
        if action == "LOGIN":
            if user and user.password == data.get("password"):
                print(f"User {username} is authenticated")
                return {"status": "success", "state": user.output_as_dict()}
            return {"status": "fail"}
        
        elif action == "UPLOAD_AVATAR":
            try:
                avatars_dir = os.path.join(ROOT_DIR, "Avatars")
                if not os.path.exists(avatars_dir):
                    os.makedirs(avatars_dir)

                img_data = base64.b64decode(data.get("file_data"))
                filepath = os.path.join(avatars_dir, f"{username}.jpg")
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                user.avatar_image_location = filepath
                print(f"Avatar for {username} saved to {filepath}")
                return {"status": "success"}
            except Exception as e:
                return {"status": "fail"}

        elif action == "SET_STATS":
            s = data.get("stats")
            user.sword_strength, user.shield_strength = s[0], s[1]
            user.slaying_potion_strength, user.healing_potion_strength = s[2], s[3]
            user.active = True
            print(f"Stats successfully assigned for user {username}.")
            self.print_fancy_table()
            return {"status": "success"}

        elif action == "GET_ACTIVE":
            active_list = {n: u.output_as_dict() for n, u in self.users.items() 
                           if u.lives > 0 and u.sword_strength != -1}
            return {"status": "success", "users": active_list}

        elif action == "DOWNLOAD_AVATAR":
            target = data.get("target")
            try:
                filepath = os.path.join(ROOT_DIR, "Avatars", f"{target}.jpg")
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    print(f"Sent {target}.jpg to {username}")
                    return {"status": "success", "file_data": encoded}
                return {"status": "fail", "msg": "File not found on server"}
            except Exception as e:
                return {"status": "fail"}

        elif action == "GET_FIGHTS":
            return {"status": "success", "fights": self.confirmed_fights}

        elif action == "FIGHT":
            boss_name = data.get("target")
            item = data.get("item")
            val = int(data.get("strength"))
            boss = self.users.get(boss_name)

            boss_def = boss.shield_strength if item == "sword" else boss.healing_potion_strength
            winner = "none"

            if boss_def == val:
                user.lives -= 1; boss.lives -= 1
                if item == "sword": user.sword_strength -= val; boss.shield_strength -= val
                else: user.slaying_potion_strength -= val; boss.healing_potion_strength -= val
            elif boss_def < val:
                winner = username
                user.lives += 1; boss.lives -= 1
                if item == "sword": user.sword_strength -= (val - boss_def); boss.shield_strength -= boss_def
                else: user.slaying_potion_strength -= (val - boss_def); boss.healing_potion_strength -= boss_def
            else: 
                winner = boss_name
                user.lives -= 1; boss.lives += 1
                if item == "sword": user.sword_strength -= val; boss.shield_strength -= (boss_def - val)
                else: user.slaying_potion_strength -= val; boss.healing_potion_strength -= (boss_def - val)

            self.confirmed_fights.append({"requester": username, "boss": boss_name, "item": item, "strength": val, "winner": winner})
            self.print_fancy_table()
            return {"status": "success", "state": user.output_as_dict()}

        return {"status": "error"}

if __name__ == "__main__":
    server = socket_server()
    server.start()