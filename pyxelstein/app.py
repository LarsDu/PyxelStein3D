import pyxel

SCREEN_HEIGHT = 256
SCREEN_WIDTH = 256
TILE_SIZE=8

# MARKERS
EMPTY = (0,0)
WALL = (1,0)
PLAYER_SPAWN_MARKER = (0,1)
PLAYER_MARKER = (1,1)


# Textures
WALL_BRICK_TEX = (4,0, 4, 4) # x,y, width, height

# Singleton Metaclass
    # NOTE: See https://stackoverflow.com/questions/6760685/
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



# Functions
def get_tile_from_world(x: float, y: float, tilemap_idx: int) -> tuple[int]:
    """
    Get tile ID tuple from world coords
    """
    return pyxel.tilemaps[tilemap_idx].pget(x//TILE_SIZE, y//TILE_SIZE)

def is_wall_tile(x: float, y: float, tilemap_idx: int) -> bool:
    """
    Check if world coords is a wall
    """
    return get_tile_from_world(x, y, tilemap_idx) == WALL

def collide_aabb(xa: float, ya: float, wa: float, ha: float, xb: float, yb: float, wb: float, hb: float) -> bool:
    """
    Return true if axis-aligned rects are overlapping, false if not overlapping.
    """
    return (
        xa < xb + wb and xa + wa > xb and ya < yb + hb and ya + ha > yb
    )
        

def cast_ray(x: float, y: float, angle: float) -> tuple[int]:
    pass

def cast_ray_visualized(x: float, y: float, angle: float) -> tuple[int]:
    pass

class OverheadCamera:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def update(self) -> None:
        pass


class Camera3d:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
    
    def update(self) -> None:
        pass

class Entity:
    def __init__(self, x: float, y: float, angle: float) -> None:
        self.x = x
        self.y = y
        self.angle = angle

    def update(self) -> None:
        raise NotImplementedError("Entity subclass must implement update method")

    def draw(self) -> None:
        raise NotImplementedError("Entity subclass must implement draw method")

class Actor:
    def __init__(self, x: float, y: float, angle: float, speed: float) -> None:
        super().__init__(x, y, angle)
        self.speed = speed
        self.manager = GameManager()

class DamageableActor(Actor):
    def __init__(self, x: float, y: float, angle: float, speed: float, hp: int) -> None:
        super().__init__(x, y, angle, speed)
        self.hp = hp

    def take_damage(self, damage: int) -> None:
        self.hp -= damage
        if self.hp <= 0:
            self.on_death()

    def on_death(self) -> None:
        pass


class Player(DamageableActor):
    def __init__(self, x: float, y: float, angle: float, speed: float = 1, hp: int = 100) -> None:
        super().__init__(x, y, angle, speed, hp)

    def update(self):
        pass

    def draw(self):
        pass


class Brownshirt(DamageableActor):
    def __init__(self, x: float, y: float, angle: float, speed: float = 1, hp: int = 20) -> None:
        super().__init__(x, y, angle, speed, hp)
    
    def update(self):
        pass

    def draw(self):
        pass

class Powerup(Entity):
    def __init__(self, x: float, y: float, angle: float) -> None:
        super().__init__(x, y, angle)

class HealthPowerup(Powerup):
    def __init__(self, x: float, y: float, angle: float, heal_amount: int) -> None:
        super().__init__(x, y, angle)
        self.heal_amount = heal_amount


class Weapon:
    def __init__(self, damage: int, fire_rate: float, ammo: int) -> None:
        self.damage = damage
        self.fire_rate = fire_rate
        self.ammo = ammo

class GameManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.score = 0

class App:
    def __init__(self) -> None:
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            caption="PyxelStein3D",
            scale=2,
            fps=60,
            quit_key=pyxel.KEY_ESCAPE,
        )
        pyxel.load("assets/pyxelstein.pyxres")

        self.init_world()
        self.manager = GameManager()
        pyxel.run(self.update, self.draw)

        def update(self):
            pass

        def draw(self):
            pass

        def init_world(self):
            pass

      

        def init_overhead_camera(self):
            pass

        def init_game_manager(self):
            pass


App()