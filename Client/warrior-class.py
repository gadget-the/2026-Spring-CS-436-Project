from tabulate import tabulate

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
        self.username = ""
        self.password = ""
        self.lives = -1
        self.avatar_image_location = ""
        self.sword_strength = -1
        self.shield_strength = -1
        self.slaying_potion_strength = -1
        self.healing_potion_strength = -1
        self.active = False

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
    
    def output_state_as_table(self):
        print("username")
        print("lives")
        print("avatar_image_location")
        print("sword_strength")
        print("shield_strength")
        print("slaying_potion_strength")
        print("healing_potion_strength")
        print("active")

if __name__ == "__main__":
    test_dict = {
        "username": "A",
        "password": "A",
        "lives": -1,
        "avatar_image_location": "",
        "sword_strength": -1,
        "shield_strength": -1,
        "slaying_potion_strength": -1,
        "healing_potion_strength": -1,
        "active": False,
        "setup_check": False
    }

    w1 = warrior()
    w1.input_from_dict(test_dict)
    # w1.output_state_as_table()

    table = [["username", "lives", "sword_strength", "shield_strength", "slaying_potion_strength", "healing_potion_strength", "active"],
        ["A", 2, -1, -1, -1, -1, False]
    ]
    print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))