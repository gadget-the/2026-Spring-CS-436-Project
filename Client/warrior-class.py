class warrior():
    username = ""
    password = ""
    lives = -1
    avatar_image_location = ""
    sword_strength = -1
    shield_strength = -1
    slaying_potion_strength = -1
    healing_potion_strength = -1
    active = False
    
    def __init__(self):
        username = ""
        password = ""
        lives = -1
        avatar_image_location = ""
        sword_strength = -1
        shield_strength = -1
        slaying_potion_strength = -1
        healing_potion_strength = -1
        active = False

    def input_from_dict(self, input_dict = {}):
        if input_dict == None:
            pass
        else:
            self.username = input_dict["username"]
            self.password = input_dict["password"]
            self.lives = input_dict["lives"]
            self.avatar_image_location = input_dict["avatar_image_location"]
            self.sword_strength = input_dict["sword_strength"]
            self.shield_strength = input_dict["shield_strength"]
            self.slaying_potion_strength = input_dict["slaying_potion_strength"]
            self.healing_potion_strength = input_dict["healing_potion_strength"]
            self.active = input_dict["active"]

    def output_as_dict(self):
        output_dict = {
            "username": self.username,
            "password": self.password,
            "lives": self.lives,
            "avatar_image_location": self.avatar_image_location,
            "sword_strength": self.sword_strength,
            "shield_strength": self.shield_strength,
            "slaying_potion_strength": self.slaying_potion_strength,
            "healing_potion_strength": self.healing_potion_strength,
            "active": self.active,
            "setup_check": False if ((self.lives <= 0) or (self.sword_strength < 0)) else True
        }
        return output_dict

if __name__ == "__main__":
    w1 = warrior()