import pygame
import json
from pygame.locals import *
import os
from utils.popups import popup
from utils.functions import create_text_surface, draw_screen, count_lines, list_png, load_json
from copy import deepcopy
import shutil


class button_class():
    def __init__(self, label, parent=None):
        """Initialize class button with name"""

        self.label = label
        self.color = (150, 150, 150)
        self.state = 0
        self.text_surface = create_text_surface(label)
        self.sub_buttons = []
        self.radius_bottom_right = -1
        self.name = label
        self.function = None
        self.parent = parent

    def hover(self, x, y):
        """Check if the given coordinates are within the menu area for hover effect"""

        if x < self.rect_value[0] or x > self.rect_value[0] + self.rect_value[2]:
            if self.state != 1:
                self.color = (150, 150, 150)
            return False
        if y < self.rect_value[1] or y > self.rect_value[1] + self.rect_value[3]:
            if self.state != 1:
                self.color = (150, 150, 150)
            return False
        if self.state != 1:
            self.color = (160, 160, 160)
        return True

    def hover_subbuttons(self, x, y):
        """hover the subbutons"""
        button_hovered = 0
        if self.state == 1:
            if self.sub_buttons is not None:
                for button in self.sub_buttons:
                    if button.hover(x, y):
                        button_hovered = 1
                    else:
                        button.color = (150, 150, 150)
        if button_hovered:
            return True

    def set_position(self, x, y, width, height):
        """set the position and size of the button and text"""

        self.rect_value = (x, y, width, height)
        text_x = x + int(width/2) - int(self.text_surface.get_width()/2)
        text_y = y + int((height - self.text_surface.get_height())/2)

        self.position_text = (text_x, text_y)

        return self

    def draw(self, screen):
        """Draw the menu on the screen"""

        pygame.draw.rect(screen, self.color, self.rect_value, border_bottom_right_radius=self.radius_bottom_right)
        screen.blit(self.text_surface, self.position_text)
        if self.state == 1:
            for button in self.sub_buttons:
                button.draw(screen)

    def click(self, x, y):
        """ Toggle the menu state and update color accordingly"""

        clicked_sub_button = 0
        if self.state == 1 and self.sub_buttons is not None:
            for button in self.sub_buttons:
                if button.click(x, y):
                    clicked_sub_button = 1
                button.state = 0

        hover = self.hover(x, y)
        if hover:
            if self.state == 0:
                self.state = 1
                self.color = (120, 120, 120)
                if self.name == "R" or self.name == "G" or self.name == "B":
                    if self.label.isalpha():
                        self.label = ""
                        self.text_surface = create_text_surface("")
            else:
                self.state = 0
                self.color = (150, 150, 150)
            if self.function is not None:

                if self.parent is not None:
                    self.parent.state = 0
                    self.grid.process_surface(self.grid.screen)
                    draw_screen(self.grid.screen, self.tab, self.grid, self.top)
                self.function()
        if clicked_sub_button:
            return True
        return hover

    def create_sub_buttons(self, sub_buttons):
        """create the sub buttons"""
        if sub_buttons is None:
            return
        count = 0
        x, y, w, h = self.rect_value
        for button_name in sub_buttons:
            count += 1
            new = button_class(button_name, self)
            new.set_position(x, (y + count * h), w, h)
            self.sub_buttons.append(new)

    def edit_label(self, key):
        """edit the label of the button using the user input(key)"""
        if key == -1:  # send -1 to erase last letter
            if len(self.label) > 0:
                self.label = self.label[:-1]
        else:
            if len(self.label) > 0:
                if int(self.label) == 0:
                    self.label = ""
            self.label += str(key)
            if int(self.label) > 255:
                self.label = "255"
        self.text_surface = create_text_surface(self.label)
        x, y, width, height = self.rect_value
        self.set_position(x, y, width, height)

    def save_tile(self):
        """save a tile as a png file"""
        new_tile = pygame.Surface((len(self.grid.tile_grid), len(self.grid.tile_grid)), pygame.SRCALPHA)
        new_tile.fill((0, 0, 0, 0))
        for line in range(len(self.grid.tile_grid)):
            for column in range(len(self.grid.tile_grid[line])):
                new_tile.set_at((column, line), self.grid.tile_grid[column][line])
        name = popup("Please choose a name for the tile:", "Tile save", self.grid, self.tab, self.top)
        if name is not None:
            pygame.image.save(new_tile, "saves/tiles/" + name + ".png")
            properties = {"traversable": self.tab.traversable_status}
            self.save_json("saves/tiles/" + name + ".json", properties)
        self.grid.tab.reload_user_tiles()

    def load_tile(self):
        """loads a tile from a png"""
        name = popup("Please choose a tile to load:", "Tile load", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/tiles/" + name + ".png"):
            image = pygame.image.load("saves/tiles/" + name + ".png")
            tile = self.grid.tile_grid = []
            for line in range(image.get_height()):
                new_line = []
                for column in range(image.get_width()):
                    new_line.append(image.get_at((line, column)))
                tile.append(new_line)
            self.grid.allow_process = 1
            self.grid.save_history_tile()

    def save_json(self, path, object):
        """saves an object to a json file"""
        with open(path, "w") as file:
            json.dump(object, file)

    def new_tile(self):
        """creates a new tile"""
        self.tab.selected_tab = 2
        self.grid.allow_process = 1
        self.grid.mode = 1
        self.grid.tile_grid = [[(0, 0, 0, 0) for x in range(16)] for y in range(16)]
        self.tab.process_tab(self.tab.screen)
        self.grid.save_history_tile()

    def save_map(self, destination=None):
        """save a map"""
        if destination is None:
            name = popup("Please choose a name for the map:", "Map save", self.grid, self.tab, self.top)
            if name is not None:
                destination = "saves/maps/" + name
            else:
                return
        tiles = {}
        pygame.image.save(self.grid.tile_surf, destination + ".png")
        for key, value in self.grid.coordinates.items():
            tiles[key] = self.get_path_from_img(value)[:-4]
        offset = self.grid.tile_offset or [0, 0]
        map_dict = {"offset": offset, "tiles": tiles}
        self.save_json(destination + ".json", map_dict)

    def get_path_from_img(self, image):
        """get the path from an image"""
        path = "./base_assets/tiles/"  # list base tiles
        tile_files = list_png(path)

        new_list = []
        for tile in tile_files:  # create an array with images and names
            img = pygame.image.load(path + tile)
            new_list.append([tile, pygame.transform.scale(img, (32, 32))])

        for tile in new_list:  # compare each image to the source image
            if self.compare_surfaces(tile[1], image):
                return "b" + tile[0]  # add b for the base tile

        path = "./saves/tiles/"  # list user tiles
        tile_files = list_png(path)

        new_list = []
        for tile in tile_files:  # create an array with images and names
            img = pygame.image.load(path + tile)
            new_list.append([tile, pygame.transform.scale(img, (32, 32))])

        for tile in new_list:  # compare each image to the source image
            if self.compare_surfaces(tile[1], image):
                return "u" + tile[0]  # add u for the user tile

    def compare_surfaces(self, s1, s2):
        """compare two surfaces"""
        if s1.get_width() != s2.get_width() or s1.get_height() != s2.get_height():
            return False

        for x in range(s1.get_width()):  # compare each pixel
            for y in range(s1.get_height()):
                if s1.get_at((x, y)) != s2.get_at((x, y)):
                    return False
        return True

    def load_map(self):
        """load a map"""
        name = popup("Please choose a map to load:", "Map load", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/maps/" + name + ".png"):
            self.grid.tile_surf = pygame.image.load("./saves/maps/" + name + ".png")
            self.grid.allow_process = 1
            self.grid.tile_offset = (0, 0)
            self.grid.save_history_map()
            if os.path.exists("./saves/maps/" + name + ".json"):
                map = load_json("./saves/maps/" + name + ".json")
                self.grid.tile_offset = map["offset"]
                self.grid.coordinates = {}
                for key, value in map["tiles"].items():
                    if value[0] == "b":
                        path = "./base_assets/tiles/" + value[1:] + ".png"
                    elif value[0] == "u":
                        path = "./saves/tiles/" + value[1:] + ".png"
                    if os.path.exists(path):
                        image = pygame.image.load(path)
                        scaled_image = pygame.transform.scale(image, (32, 32))
                        self.grid.coordinates[key] = scaled_image


    def new_map(self):
        self.grid.set = None
        self.grid.tile_surf = pygame.Surface((self.grid.tile_size, self.grid.tile_size), pygame.SRCALPHA)  # create a starting surface of tile size
        self.grid.tile_surf.fill((0, 0, 0, 0))
        self.grid.allow_process = 1
        self.grid.save_history_map()
        self.grid.coordinates = {}

    def delete_tile(self):
        """delete a tile"""
        name = popup("Please choose a tile to delete:", "Tile delete", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/tiles/" + name + ".png"):
            os.remove("./saves/tiles/" + name + ".png")

    def delete_map(self):
        """delete a map"""
        name = popup("Please choose a map to delete:", "Map delete", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/maps/" + name + ".png"):
            os.remove("./saves/maps/" + name + ".png")

    def undo(self):
        if self.grid.mode == 0:
            if self.grid.undo_index_map != len(self.grid.history_map) - 1:
                self.grid.undo_index_map += 1
                self.grid.tile_surf = self.grid.history_map[self.grid.undo_index_map][0].copy()
                self.grid.tile_offset = self.copy_tuple(self.grid.history_map[self.grid.undo_index_map][1])
        elif self.grid.mode == 1:
            if self.grid.undo_index_tile != len(self.grid.history_tile) - 1:
                self.grid.undo_index_tile += 1
                self.grid.tile_grid = deepcopy(self.grid.history_tile[self.grid.undo_index_tile])
        self.grid.allow_process = 1

    def redo(self):
        if self.grid.mode == 0:
            if self.grid.undo_index_map != 0:
                self.grid.undo_index_map -= 1
                self.grid.tile_surf = self.grid.history_map[self.grid.undo_index_map][0].copy()
                self.grid.tile_offset = self.copy_tuple(self.grid.history_map[self.grid.undo_index_map][1])
        elif self.grid.mode == 1:
            if self.grid.undo_index_tile != 0:
                self.grid.undo_index_tile -= 1
                self.grid.tile_grid = deepcopy(self.grid.history_tile[self.grid.undo_index_tile])
        self.grid.allow_process = 1

    def activate_grid(self):
        self.grid.grid_status += 1  # status changes in a loop
        self.grid.grid_status %= 3  # 0 -> 1 -> 2 -> 0

        if self.grid.grid_status == 0:
            self.label = "Grid OFF"
        elif self.grid.grid_status == 1:
            self.label = "Grid UNDER"
        elif self.grid.grid_status == 2:
            self.label = "Grid ON"

        self.text_surface = create_text_surface(self.label)
        self.set_position(*self.rect_value)

        self.tab.process_tab(self.tab.screen)
        self.grid.allow_process = 1

    def activate_traversable(self):
        self.tab.traversable_status += 1  # status changes in a loop
        self.tab.traversable_status %= 2  # 0 -> 1 -> 0

        if self.tab.traversable_status == 0:
            self.label = "Traversable OFF"
        elif self.tab.traversable_status == 1:
            self.label = "Traversable ON"

        self.text_surface = create_text_surface(self.label)
        self.set_position(*self.rect_value)

        self.tab.process_tab(self.tab.screen)

    @staticmethod
    def copy_tuple(target):
        if target is None:
            return None
        return (target[0], target[1])

    def change_tab(self):
        """Check which tab menu is clicked and set the selected tab accordingly"""
        if self.label == "Map mode":
            self.tab.selected_tab = 1
            self.grid.mode = 0
            self.grid.allow_process = 1
        elif self.label == "Tile mode":
            self.tab.selected_tab = 2
            self.grid.mode = 1
            self.grid.allow_process = 1
        elif self.label == "Settings":
            self.tab.selected_tab = 3
        elif self.label == "Project":
            self.tab.selected_tab = 4
        elif self.label == "Entities":
            self.tab.selected_tab = 5
        elif self.label == "Events":
            self.tab.selected_tab = 6

    def new_project(self):
        name = popup("Please choose a name for the project:", "New project", self.grid, self.tab, self.top)
        if name is not None and not os.path.exists("./saves/projects/" + name):
            self.tab.project_name = name
            os.makedirs("./saves/projects/" + name)
            os.makedirs("./saves/projects/" + name + "/maps/")
            self.tab.process_tab(self.tab.screen)

    def delete_project(self):
        """delete a project"""
        name = popup("Please choose a project to delete:", "Project delete", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/projects/" + name):
            shutil.rmtree("./saves/projects/" + name)

    def load_project(self):
        """load a project"""
        name = popup("Please choose a project to load:", "Project load", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/projects/" + name):
            self.tab.project_name = name
            self.tab.map_list = []
            for map in os.listdir("./saves/projects/" + self.tab.project_name + "/maps/"):
                self.tab.map_list.append(map)
            self.tab.process_tab(self.tab.screen)

    def link_map_to_project(self):

        name = popup("Please choose a map to link:", "Map link", self.grid, self.tab, self.top)

        if name is not None:
            source = "./saves/maps/" + name + ".png"
            dest = "./saves/projects/" + self.tab.project_name + "/maps/" + name + ".png"

            if os.path.exists(source):
                shutil.copy(source, dest)
                self.tab.map_list.append(name)

    def new_blueprint(self):
        self.new_map()

    def load_blueprint(self):
        """loads a blueprint"""
        name = popup("Please choose a blueprint to load:", "Blueprint load", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/blueprints/" + name + ".png"):
            self.grid.tile_surf = pygame.image.load("./saves/blueprints/" + name + ".png")
            self.grid.allow_process = 1
            self.grid.tile_offset = (0, 0)
            self.grid.save_history_map()

    def save_blueprint(self):
        """saves a blueprint"""
        name = popup("Please choose a name for the blueprint:", "Blueprint save", self.grid, self.tab, self.top)
        if name is not None:
            pygame.image.save(self.grid.tile_surf, "./saves/blueprints/" + name + ".png")
            self.grid.tab.reload_blueprints()

    def delete_blueprint(self):
        """deletes a blueprint"""
        name = popup("Please choose a blueprint to delete:", "Blueprint delete", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/blueprints/" + name + ".png"):
            os.remove("./saves/blueprints/" + name + ".png")
            self.grid.tab.reload_blueprints()

    def dropdown_function(self):
        if self.label.startswith("Base tiles"):
            self.tab.dropdown_base_tiles = not self.tab.dropdown_base_tiles
        elif self.label.startswith("User tiles"):
            self.tab.dropdown_user_tiles = not self.tab.dropdown_user_tiles
        elif self.label.startswith("Blueprints"):
            self.tab.dropdown_blueprints = not self.tab.dropdown_blueprints

        position = self.tab.drop_downs[0].rect_value[1]
        lines = 0
        if self.tab.dropdown_base_tiles:
            lines = count_lines(self.tab.tiles)

        position += 30 + 40 * lines
        self.tab.drop_downs[1].set_position(10, position, 300, 20)
        lines = 0

        if self.tab.dropdown_user_tiles:
            lines = count_lines(self.tab.user_tiles)

        position += 30 + 40 * lines
        self.tab.drop_downs[2].set_position(10, position, 300, 20)

    @staticmethod
    def help():
        import subprocess
        try:  # Run the wslpath command and capture the output
            path = './base_assets/index.html'
            result = subprocess.run(['wslpath', '-w', path], capture_output=True, text=True, check=True)
            windows_path = result.stdout.strip()
            subprocess.run(['wslview', windows_path])
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def new_event(self):
        pass

    def play(self):
        import subprocess
        self.autosave()
        subprocess.run(['./utils/game_template.py', './saves/autosave_map.png'])

    def autosave(self):
        """save the map"""
        self.save_map("saves/autosave_map")

        """save the tile"""
        new_tile = pygame.Surface((len(self.grid.tile_grid), len(self.grid.tile_grid)), pygame.SRCALPHA)
        new_tile.fill((0, 0, 0, 0))
        for line in range(len(self.grid.tile_grid)):
            for column in range(len(self.grid.tile_grid[line])):
                new_tile.set_at((column, line), self.grid.tile_grid[column][line])
        pygame.image.save(new_tile, "saves/autosave_tile.png")
        """save entities"""
        self.save_entities("./saves/autosave_entities.json")

    def select_skin(self):
        name = popup("Please choose a tile as a skin for the entity", "Change skin", self.grid, self.tab, self.top)
        if name is not None and os.path.exists("./saves/tiles/" + name + ".png"):
            self.tab.selected_entity["skin"] = name
            self.grid.allow_process = 1

    def add_stat(self):
        pass

    def save_entities(self, path):
        """save the entities in json file"""
        entities = self.grid.entities.copy()
        entities.append({"skin": "rabbit", "position": [5, 5], "keys": [1073741906, 1073741903, 1073741905, 1073741904]})
        self.save_json(path, entities)
