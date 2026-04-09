import sys
import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from socket_client_class import socket_client

PLAYERS_DIR = "players" 
os.makedirs(PLAYERS_DIR, exist_ok=True)

def get_player_dir(username):
    path = os.path.join(PLAYERS_DIR, username) 
    os.makedirs(path, exist_ok=True)
    return path

def fmt(val):
    return "unassigned" if val == -1 else str(val)

def print_warrior_state(w):
    print("\n" + "="*44)
    print(f"  Warrior: {w['username']}")
    print("="*44)
    print(f"  {'Lives':<22} {w['lives']}")
    print(f"  {'Sword':<22} {fmt(w['sword_strength'])}")
    print(f"  {'Shield':<22} {fmt(w['shield_strength'])}")
    print(f"  {'Slaying Potion':<22} {fmt(w['slaying_potion_strength'])}")
    print(f"  {'Healing Potion':<22} {fmt(w['healing_potion_strength'])}")
    print("="*44 + "\n")

def print_active_warriors_table(warriors_list):
    if not warriors_list:
        print("\n  (no other active warriors)\n")
        return
    col = [14, 7, 7, 16, 16, 6]
    header  = f"  {'Username':<{col[0]}} {'Sword':>{col[1]}} {'Shield':>{col[2]}} {'Slaying Pot':>{col[3]}} {'Healing Pot':>{col[4]}} {'Lives':>{col[5]}}"
    divider = "  " + "-" * (sum(col) + len(col))
    print("\n" + divider)
    print(header)
    print(divider)
    for w in warriors_list:
        print(f"  {w['username']:<{col[0]}} {fmt(w['sword_strength']):>{col[1]}} {fmt(w['shield_strength']):>{col[2]}} {fmt(w['slaying_potion_strength']):>{col[3]}} {fmt(w['healing_potion_strength']):>{col[4]}} {str(w['lives']):>{col[5]}}")
    print(divider + "\n")

def print_fight_requests_table(requests):
    if not requests:
        print("\n  (no confirmed fight requests yet)\n")
        return
    col = [12, 12, 16, 8, 12]
    header  = f"  {'Requester':<{col[0]}} {'Boss':<{col[1]}} {'Item':<{col[2]}} {'Str':>{col[3]}} {'Winner':<{col[4]}}"
    divider = "  " + "-" * (sum(col) + len(col))
    print("\n" + divider)
    print(header)
    print(divider)
    for r in requests:
        print(f"  {r['requester']:<{col[0]}} {r['boss']:<{col[1]}} {r['fighting_item']:<{col[2]}} {str(r['fighting_item_strength']):>{col[3]}} {r['winner']:<{col[4]}}")
    print(divider + "\n")

def login(client):
    while True:
        username = input("  Username: ").strip()
        password = input("  Password: ").strip()
        client.send_json({"action": "login", "username": username, "password": password})
        resp = client.receive_json()

        if resp["status"] == "accepted":
            print(f"\n  Login successful! Welcome, warrior {username}.")
            return username, resp["warrior"]

        if resp["status"] == "game_over":
            print("\n  GAME OVER - this warrior has no lives remaining.")
            return username, None

        print(f"\n  Login rejected: {resp.get('reason', 'invalid credentials')}")
        print("  1) Try again")
        print("  2) Quit")
        choice = input("  > ").strip()
        if choice != "1":
            return None, None

def upload_avatar(client, username):
    ans = input("  Upload avatar image? (y/n): ").strip().lower()
    if ans != "y":
        return
    filename = input("  Enter image filename (e.g. A.jpg): ").strip()
    if not os.path.exists(filename):
        print(f"  File '{filename}' not found. Skipping.")
        return
    client.send_json({"action": "avatar_upload", "username": username})
    client.send_file(filename)
    resp = client.receive_json()
    if resp["status"] == "ok":
        print(f"  Avatar uploaded and saved as {username}.jpg on server.")
    else:
        print("  Avatar upload failed.")

def assign_strengths(client, username):
    print("\n  You are given 10 strengths.")
    print("  Assign values [0-3] to each item. Total must equal exactly 10.\n")
    while True:
        try:
            sword   = int(input("  Sword strength     [0-3]: ").strip())
            shield  = int(input("  Shield strength    [0-3]: ").strip())
            slaying = int(input("  Slaying potion     [0-3]: ").strip())
            healing = int(input("  Healing potion     [0-3]: ").strip())
        except ValueError:
            print("  Please enter whole numbers only.\n")
            continue

        if any(v < 0 or v > 3 for v in [sword, shield, slaying, healing]):
            print("  Each value must be 0, 1, 2, or 3. Try again.\n")
            continue

        total = sword + shield + slaying + healing
        if total != 10:
            print(f"  Total is {total} - must be exactly 10. Try again.\n")
            continue

        client.send_json({
            "action":          "assign_strengths",
            "username":        username,
            "sword":           sword,
            "shield":          shield,
            "slaying_potion":  slaying,
            "healing_potion":  healing
        })
        resp = client.receive_json()
        if resp["status"] == "ok":
            print("\n  Strengths assigned!")
            return resp["warrior"]
        print("  Server rejected assignment. Try again.\n")

def download_avatar(client, username, active_names, player_dir):
    if not active_names:
        return
        
    ans = input("  Download another warrior's avatar? (y/n): ").strip().lower()
    if ans != "y":
        return
    target = input(f"  Enter username ({', '.join(active_names)}): ").strip()
    if target not in active_names:
        print("  Invalid username.")
        return
    client.send_json({"action": "avatar_download", "username": username, "target": target})
    resp = client.receive_json()
    if resp["status"] != "ok":
        print(f"  Error: {resp.get('reason')}")
        return
    client.send_message("READY") 
    save_path = os.path.join(player_dir, f"{target}.jpg") 
    if client.receive_file(save_path):
        print(f"  Avatar saved to {save_path}")
    else:
        print("  Download failed.")

def send_fight_request(client, username, warrior_state, active_names):
    print("\n  Other active warriors:")
    if not active_names:
        print("    (no other active warriors)")
        return warrior_state
        
    for name in active_names:
        print(f"    - {name}")

    boss = input("  Who do you want to fight? ").strip()
    if boss not in active_names:
        print("  Invalid target.")
        return warrior_state

    print("  Fighting item:")
    print("    1) Sword")
    print("    2) Slaying Potion")
    choice = input("  > ").strip()
    if choice == "1":
        item  = "sword"
        avail = warrior_state["sword_strength"]
    elif choice == "2":
        item  = "slaying_potion"
        avail = warrior_state["slaying_potion_strength"]
    else:
        print("  Invalid choice.")
        return warrior_state

    if avail <= 0:
        print(f"  You have no {item} strength left. Cannot fight.")
        return warrior_state

    try:
        strength = int(input(f"  Strength to use [1-{avail}]: ").strip())
    except ValueError:
        print("  Invalid input.")
        return warrior_state

    if strength <= 0 or strength > avail:
        print(f"  Must be between 1 and {avail}.")
        return warrior_state

    client.send_json({
        "action":   "fight",
        "username": username,
        "boss":     boss,
        "item":     item,
        "strength": strength
    })
    resp = client.receive_json()

    if resp["status"] == "rejected":
        print(f"  Fight rejected: {resp.get('reason')}")
        return warrior_state

    winner = resp["winner"]
    if winner == "requester":
        print(f"\n  YOU WIN against {boss}! You gain a life.")
    elif winner == "boss":
        print(f"\n  You LOST to {boss}. You lose a life.")
    else:
        print(f"\n  TIE with {boss}. Both lose a life.")

    updated = resp["warrior"]
    print_warrior_state(updated)
    return updated

def run_client():
    client = socket_client(givenName='localhost', givenPort=12000)
    print("\n" + "="*44)
    print("   Welcome to the RPG Warrior Game!")
    print("="*44 + "\n")

    username, warrior_state = login(client)
    if username is None:
        print("  Goodbye!")
        client.stop()
        return
    if warrior_state is None:
        client.stop()
        return

    player_dir = get_player_dir(username) 
    print_warrior_state(warrior_state)

    upload_avatar(client, username)

    if warrior_state["sword_strength"] == -1: 
        warrior_state = assign_strengths(client, username)
        print_warrior_state(warrior_state)

    ans = input("  View list of other active warriors? (y/n): ").strip().lower()
    if ans != "y":
        print("  Goodbye!")
        client.stop()
        return

    client.send_json({"action": "get_active_list", "username": username})
    resp = client.receive_json()
    
    active_names = resp.get("active_warriors", [])
    if isinstance(active_names, str) and active_names == "No active warriors":
        active_names = []
        
    # exclude current user
    active_names = [name for name in active_names if name != username]

    if not active_names:
        print("\n  No other active warriors yet. Goodbye!")
        client.stop()
        return

    print(f"\n  Other active warriors: {', '.join(active_names)}")

    download_avatar(client, username, active_names, player_dir) 

    client.send_json({"action": "get_fight_requests", "username": username})
    resp = client.receive_json()
    print("\n  === Confirmed Fight Requests ===")
    print_fight_requests_table(resp.get("fight_requests", []))

    while warrior_state["lives"] > 0:
        ans = input("  Send a fight request? (y/n): ").strip().lower()
        if ans != "y":
            break

        client.send_json({"action": "get_active_list", "username": username}) 
        resp = client.receive_json()
        active_names = resp.get("active_warriors", [])
        
        if isinstance(active_names, str) and active_names == "No active warriors":
            active_names = []
            
        # exclude current user
        active_names = [name for name in active_names if name != username]

        if not active_names:
            print("  No other active warriors to fight.")
            break

        warrior_state = send_fight_request(client, username, warrior_state, active_names)
        if warrior_state["lives"] <= 0:
            print("  You have no lives left. Game over!")
            break

    ans = input("  View full info on all other active warriors? (y/n): ").strip().lower()
    if ans == "y":
        client.send_json({"action": "get_active_full", "username": username})
        resp = client.receive_json()
        all_warriors = resp.get("active_warriors", [])
        
        # exclude current user from table
        other_warriors = [w for w in all_warriors if w.get("username") != username]
        
        print("\n  === Other Active Warriors ===")
        print_active_warriors_table(other_warriors)

    print("  Thanks for playing! Goodbye.")
    client.stop()

if __name__ == "__main__":
    run_client()