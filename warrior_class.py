class warrior():
    def __init__(self, username = "", password = ""):
        self.username = username
        self.password = password
        self.lives = 2
        self.avatar_image_location = ""
        self.sword_strength = -1
        self.shield_strength = -1
        self.slaying_potion_strength = -1
        self.healing_potion_strength = -1
        self.active = False
    
    def update_activity(self):
        # A warrior is alive if they have enough lives and have a sword
        if self.sword_strength >= 0 and self.lives > 0:
            self.active = True
        else:
            self.active = False

    def input_from_dict(self, input_dict):
        if input_dict:
            self.username = input_dict.get("username", self.username)
            self.password = input_dict.get("password", self.password)
            self.lives = input_dict.get("lives", self.lives)
            self.avatar_image_location = input_dict.get("avatar_image_location", self.avatar_image_location)
            self.sword_strength = input_dict.get("sword_strength", self.sword_strength)
            self.shield_strength = input_dict.get("shield_strength", self.shield_strength)
            self.slaying_potion_strength = input_dict.get("slaying_potion_strength", self.slaying_potion_strength)
            self.healing_potion_strength = input_dict.get("healing_potion_strength", self.healing_potion_strength)
            self.update_activity()

    def output_as_dict(self):
        self.update_activity()
        return {
            "username": self.username, # might not need the username attr, the way the code is set up
            "password": self.password,
            "lives": self.lives,
            "avatar_image_location": self.avatar_image_location,
            "sword_strength": self.sword_strength,
            "shield_strength": self.shield_strength,
            "slaying_potion_strength": self.slaying_potion_strength,
            "healing_potion_strength": self.healing_potion_strength,
            "active": self.active
        }