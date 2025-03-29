import pyxel

SCREEN_HEIGHT = 240
SCREEN_WIDTH = 256

# MARKERS
EMPTY = (0,0)
WALL = (1,0)
PLAYER_SPAWN_MARKER = (0,1)
PLAYER_MARKER = (1,1)


# Textures
WALL_BRICK_TEX = (4,0, 4, 4) # x,y, width, height




class OverheadCamera:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def update(self):
        pass



class App:
    def __init__(self) -> None:
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            caption="PyxelStein3D",
            scale=1,
            fps=60,
            quit_key=pyxel.KEY_ESCAPE,
        )
        pyxel.load("assets/pyxelstein.pyxres")

        self.init_rooms()
        self.init_player()
        self.init_overhead_camera()
        self.init_game_manager()
        pyxel.run(self.update, self.draw)

        def update(self):
            pass

        def draw(self):
            pass