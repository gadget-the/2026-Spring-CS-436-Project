import sys
import os
import json
import base64
from socket import socket, AF_INET, SOCK_DGRAM

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from warrior_class import warrior

SERVER_PORT  = 12000
AVATARS_DIR  = os.path.join(ROOT_DIR, "Avatars") # use the existing Avatars/ folder at root
PLAYERS_DIR  = os.path.join(ROOT_DIR, "players") # players/A/, players/B/ etc at root
CHUNK_SIZE   = 1024
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', SERVER_PORT))

def send(msg, addr):
    serverSocket.sendto(msg.encode(), addr)

def send_json(obj, addr):
    send(json.dumps(obj), addr)

def recv():
    data, addr = serverSocket.recvfrom(65535)
    return data.decode(), addr

def recv_bytes():
    data, addr = serverSocket.recvfrom(CHUNK_SIZE + 64)
    return data, addr

def get_player_dir(username):
    path = os.path.join(PLAYERS_DIR, username)
    os.makedirs(path, exist_ok=True)
    return path

def make_warrior(username):
    w = warrior()
    w.username = username
    w.password = username # password same as username
    w.lives    = 2
    return w

warriors = {u: make_warrior(u) for u in ["A", "B", "C", "D"]}
fight_requests = [] # confirmed fight history

def receive_file_from_client(save_path, client_addr):
    header, _ = recv()
    if not header.startswith("FILESTART:"):
        return False
    total = int(header.split(":")[1])
    send("FILESTART_ACK", client_addr)
    received = b""
    while len(received) < total:
        chunk, _ = recv_bytes()
        received += chunk
        send("CHUNK_ACK", client_addr) # ack
    end_marker, _ = recv()
    if end_marker == "FILEEND":
        with open(save_path, "wb") as f:
            f.write(received)
        send("FILEEND_ACK", client_addr)
        return True
    return False

def send_file_to_client(filepath, client_addr):
    with open(filepath, "rb") as f:
        data = f.read()
    total = len(data)
    send(f"FILESTART:{total}", client_addr)
    ack, _ = recv()
    if ack != "FILESTART_ACK":
        return False
    offset = 0
    while offset < total:
        chunk = data[offset:offset + CHUNK_SIZE]
        serverSocket.sendto(chunk, client_addr)
        recv() # wait for ack
        offset += CHUNK_SIZE
    send("FILEEND", client_addr)
    ack, _ = recv()
    return ack == "FILEEND_ACK"

def resolve_fight(attacker, defender, item, strength):
    def_stat = defender.shield_strength if item == "sword" else defender.healing_potion_strength

    if def_stat == strength: # tie - both lose a life
        attacker.lives -= 1
        defender.lives -= 1
        att_cost = strength  # attacker loses full attack amount
        def_cost = def_stat  # defender loses full defense amount
        winner = "none"
    elif strength > def_stat: # attacker wins
        attacker.lives += 1
        defender.lives -= 1
        att_cost = def_stat  # attacker only loses what defender had
        def_cost = def_stat  # defender loses their full defense stat
        winner = "requester"
    else: # defender wins - def_stat > strength
        attacker.lives -= 1
        defender.lives += 1
        att_cost = strength  # attacker loses full attack amount
        def_cost = strength  # defender also loses the attack amount
        winner = "boss"

    if item == "sword":
        attacker.sword_strength  -= att_cost
        defender.shield_strength -= def_cost
    else:
        attacker.slaying_potion_strength -= att_cost
        defender.healing_potion_strength -= def_cost

    for w in [attacker, defender]: # set strength min
        for attr in ["sword_strength", "shield_strength", "slaying_potion_strength", "healing_potion_strength"]:
            if getattr(w, attr) < 0:
                setattr(w, attr, 0)
        w.active = (w.lives > 0 and w.sword_strength >= 0)

    return winner

def get_active_warriors(exclude=None):
    return [w for u, w in warriors.items() if u != exclude and w.lives > 0 and w.sword_strength >= 0]

def handle_login(payload, addr):
    u = payload["username"]
    p = payload["password"]
    print(f"[SERVER] Received login request from user {u}")

    if u not in warriors or warriors[u].password != p:
        send_json({"status": "rejected", "reason": "Invalid credentials"}, addr)
        print(f"[SERVER] Rejected login for user {u}")
        return

    print(f"[SERVER] User {u} is authenticated")
    w = warriors[u]

    if w.lives <= 0:
        send_json({"status": "game_over"}, addr)
        print(f"[SERVER] Game over - sent message to user {u}")
        return

    get_player_dir(u) # create players/A/ on first login if it doesn't exist yet
    send_json({"status": "accepted", "warrior": w.output_as_dict()}, addr)
    print(f"[SERVER] Sent warrior state to user {u}")
    print_warriors_table("Current warrior states", warriors)

def handle_avatar_upload(payload, addr):
    u = payload["username"]
    save_path = os.path.join(AVATARS_DIR, f"{u}.jpg") # stored in Avatars/(their choice).jpg
    print(f"[SERVER] Receiving avatar upload from user {u}")
    if receive_file_from_client(save_path, addr):
        warriors[u].avatar_image_location = save_path
        send_json({"status": "ok"}, addr)
        print(f"[SERVER] Stored avatar for user {u} as {u}.jpg")
    else:
        send_json({"status": "error"}, addr)

def handle_assign_strengths(payload, addr):
    u = payload["username"]
    w = warriors[u]
    print(f"[SERVER] Received strength assignment from user {u}")
    w.sword_strength          = payload["sword"]
    w.shield_strength         = payload["shield"]
    w.slaying_potion_strength = payload["slaying_potion"]
    w.healing_potion_strength = payload["healing_potion"]
    w.active = True
    send_json({"status": "ok", "warrior": w.output_as_dict()}, addr)
    print(f"[SERVER] Strength assignment stored for user {u}")
    print_warriors_table("Current warrior states", warriors)

def handle_get_active_list(payload, addr):
    u      = payload["username"]
    active = get_active_warriors(exclude=u)
    names  = [u] + [w.username for w in active] # include the requesting client
    send_json({"status": "ok", "active_warriors": names}, addr)
    print(f"[SERVER] Sent active warrior list to user {u}: {names}")

def handle_get_active_full(payload, addr):
    u      = payload["username"]
    active = get_active_warriors(exclude=u)
    self_data = [warriors[u].output_as_dict()] # include the requesting user at the top
    data   = self_data + [w.output_as_dict() for w in active]
    send_json({"status": "ok", "active_warriors": data}, addr)
    print(f"[SERVER] Sent full active warrior info to user {u}")

def handle_avatar_download(payload, addr):
    u      = payload["username"]
    target = payload["target"]
    path   = os.path.join(AVATARS_DIR, f"{target}.jpg") # pull from Avatars/ folder
    print(f"[SERVER] User {u} requested avatar of {target}")
    if not os.path.exists(path):
        send_json({"status": "error", "reason": "Avatar not found"}, addr)
        print(f"[SERVER] Avatar for {target} not found")
        return
    send_json({"status": "ok"}, addr)
    recv() # wait for client
    send_file_to_client(path, addr)
    print(f"[SERVER] Sent avatar of {target} to user {u}")

def handle_get_fight_requests(payload, addr):
    u = payload["username"]
    send_json({"status": "ok", "fight_requests": fight_requests}, addr)
    print(f"[SERVER] Sent list of confirmed fight requests to user {u}")

def handle_fight(payload, addr):
    req_name  = payload["username"]
    boss_name = payload["boss"]
    item      = payload["item"]     # user choice
    strength  = payload["strength"]
    print(f"[SERVER] Received fight request from user {req_name} against {boss_name} using {item} strength {strength}")

    attacker = warriors.get(req_name)
    defender = warriors.get(boss_name)

    if not attacker or not defender:
        send_json({"status": "rejected", "reason": "Invalid warrior"}, addr)
        return

    avail = attacker.sword_strength if item == "sword" else attacker.slaying_potion_strength

    if strength <= 0 or strength > avail:
        send_json({"status": "rejected", "reason": f"Insufficient {item} strength (have {avail})"}, addr)
        print(f"[SERVER] Rejected fight request from {req_name}: not enough {item} strength")
        return

    winner = resolve_fight(attacker, defender, item, strength)

    fight_requests.append({ # store confirmed request in history
        "requester":              req_name,
        "boss":                   boss_name,
        "fighting_item":          item,
        "fighting_item_strength": strength,
        "winner":                 winner
    })
    print(f"[SERVER] Confirmed fight request for user {req_name}. Winner: {winner}")
    print_warriors_table("Updated warrior states after fight", warriors)

    send_json({"status": "ok", "winner": winner, "warrior": attacker.output_as_dict()}, addr)

def print_warriors_table(label, warriors_dict):
    col = [8, 7, 7, 12, 12, 6]
    header  = f"  {'User':<{col[0]}} {'Sword':>{col[1]}} {'Shield':>{col[2]}} {'Slay Pot':>{col[3]}} {'Heal Pot':>{col[4]}} {'Lives':>{col[5]}}"
    divider = "  " + "-" * (sum(col) + len(col))
    print(f"\n[SERVER] {label}")
    print(divider)
    print(header)
    print(divider)
    for u, w in warriors_dict.items():
        sword  = "unset" if w.sword_strength  < 0 else str(w.sword_strength)
        shield = "unset" if w.shield_strength < 0 else str(w.shield_strength)
        slay   = "unset" if w.slaying_potion_strength < 0 else str(w.slaying_potion_strength)
        heal   = "unset" if w.healing_potion_strength < 0 else str(w.healing_potion_strength)
        status = "ACTIVE" if (w.lives > 0 and w.sword_strength >= 0) else "inactive"
        print(f"  {u:<{col[0]}} {sword:>{col[1]}} {shield:>{col[2]}} {slay:>{col[3]}} {heal:>{col[4]}} {str(w.lives):>{col[5]}}  [{status}]")
    print(divider + "\n")

def start_server():
    print(f"[SERVER] RPG server ready on port {SERVER_PORT}")
    while True:
        raw, client_addr = recv()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[SERVER] Malformed message from {client_addr}")
            continue

        action = payload.get("action", "")
        if   action == "login":              handle_login(payload, client_addr)
        elif action == "avatar_upload":      handle_avatar_upload(payload, client_addr)
        elif action == "assign_strengths":   handle_assign_strengths(payload, client_addr)
        elif action == "get_active_list":    handle_get_active_list(payload, client_addr)
        elif action == "get_active_full":    handle_get_active_full(payload, client_addr)
        elif action == "avatar_download":    handle_avatar_download(payload, client_addr)
        elif action == "get_fight_requests": handle_get_fight_requests(payload, client_addr)
        elif action == "fight":              handle_fight(payload, client_addr)
        elif action == "STOP":
            print("[SERVER] Shutdown signal received.")
            break
        else:
            print(f"[SERVER] Unknown action '{action}' from {client_addr}")

if __name__ == "__main__":
    start_server()