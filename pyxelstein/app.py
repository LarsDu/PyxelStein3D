import pyxel

SCREEN_HEIGHT = 256
SCREEN_WIDTH = 256
TILE_SIZE = 8
MAX_CAST_DISTANCE = 1024  # in world length, not tile length
RAY_CAST_ARC_DEG: float = 90

COL_TRANSPARENT_BLACK = 0
COL_TRANSPARENT_PURP = 2

# MARKERS
EMPTY = (0, 0)
WALL = (1, 0)
PLAYER_SPAWN_MARKER = (0, 1)
PLAYER_MARKER = (1, 1)


# Textures
WALL_BRICK_TEX = (4, 0, 4, 4)  # x,y, width, height


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
    return pyxel.tilemaps[tilemap_idx].pget(x // TILE_SIZE, y // TILE_SIZE)


def is_solid_tile(x: float, y: float, tilemap_idx: int) -> bool:
    """
    Check if world coords is a wall
    """
    return get_tile_from_world(x, y, tilemap_idx) == WALL


def pushback_solid_tile(
    x: float, y: float, w: float, h: float, dx: float, dy: float, tilemap_idx: int
) -> tuple[float, float, float, float]:
    """Compute new_x, new_y, new_dx, new_dy pushback from solid tile collision"""
    nx, ny = x + dx, y + dy
    ndx, ndy = dx, dy

    # FIXME: Only call function if needed
    top_right = is_solid_tile(nx + w, ny, tilemap_idx)
    top_left = is_solid_tile(nx, ny, tilemap_idx)
    bottom_right = is_solid_tile(nx + w, ny + h, tilemap_idx)
    bottom_left = is_solid_tile(nx, ny + h, tilemap_idx)

    if dx > 0:
        if top_right or bottom_right:
            ndx = 0  # Set velocity to 0
            nx -= dx  # Undo the move
    elif dx < 0:
        if top_left or bottom_left:
            ndx = 0
            nx -= dx

    if dy > 0:
        if bottom_left or bottom_right:
            ndy = 0
            ny -= dy
    elif dy < 0:
        if top_left or top_right:
            ndy = 0
            ny -= dy
    return (nx, ny, ndx, ndy)


def collide_aabb(
    xa: float,
    ya: float,
    wa: float,
    ha: float,
    xb: float,
    yb: float,
    wb: float,
    hb: float,
) -> bool:
    """
    Return true if axis-aligned rects are overlapping, false if not overlapping.
    """
    return xa < xb + wb and xa + wa > xb and ya < yb + hb and ya + ha > yb


def cast_ray_basic(
    x: float, y: float, rot: float, step: int = TILE_SIZE, tilemap_idx: int = 0
) -> tuple[float, float]:
    dx = step * pyxel.cos(rot)
    dy = step * pyxel.sin(rot)
    hx, hy = x, y
    for _ in range(MAX_CAST_DISTANCE // step):
        hx += dx
        hy += dy
        if is_solid_tile(hx, hy, tilemap_idx=tilemap_idx):
            # TODO: Calculate nearest intercept with solid tile from ray
            break
    # If no hit found
    return hx, hy


def cast_ray(
    x: float, y: float, rot: float, tilemap_idx: int = 0
) -> tuple[float, float]:
    # Ray direction vector
    ray_dir_x = pyxel.cos(rot)
    ray_dir_y = pyxel.sin(rot)

    # Which tile of the map we're in
    map_x = int(x // TILE_SIZE)
    map_y = int(y // TILE_SIZE)

    # Length of ray from current position to next x or y-side
    side_dist_x = 0.0
    side_dist_y = 0.0

    # Length of ray from one x or y-side to next x or y-side
    delta_dist_x = float("inf") if ray_dir_x == 0 else abs(1 / ray_dir_x)
    delta_dist_y = float("inf") if ray_dir_y == 0 else abs(1 / ray_dir_y)

    # What direction to step in x or y-direction (either +1 or -1)
    step_x = 1 if ray_dir_x >= 0 else -1
    step_y = 1 if ray_dir_y >= 0 else -1

    # Calculate initial side_dist values
    if ray_dir_x < 0:
        side_dist_x = (x / TILE_SIZE - map_x) * delta_dist_x
    else:
        side_dist_x = (map_x + 1.0 - x / TILE_SIZE) * delta_dist_x

    if ray_dir_y < 0:
        side_dist_y = (y / TILE_SIZE - map_y) * delta_dist_y
    else:
        side_dist_y = (map_y + 1.0 - y / TILE_SIZE) * delta_dist_y

    # DDA algorithm
    side = 0  # 0 for x-side, 1 for y-side
    hit = False

    for _ in range(MAX_CAST_DISTANCE):
        # Jump to next map square, either in x-direction, or in y-direction
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1

        # Check if ray hit a wall
        if is_solid_tile(
            map_x * TILE_SIZE + TILE_SIZE // 2,
            map_y * TILE_SIZE + TILE_SIZE // 2,
            tilemap_idx=tilemap_idx,
        ):
            hit = True
            break

    # If we didn't hit anything, return the maximum distance point
    if not hit:
        return (x + ray_dir_x * MAX_CAST_DISTANCE, y + ray_dir_y * MAX_CAST_DISTANCE)

    # Calculate exact hit position - this is the key fix
    if side == 0:  # X-side was hit (vertical wall)
        # The exact distance to the hit point
        perp_wall_dist = (map_x - x / TILE_SIZE + (1 - step_x) / 2) / ray_dir_x

        # Calculate the exact hit point on the wall
        hit_x = map_x * TILE_SIZE
        # If we're stepping right, hit is on left side of new tile; if stepping left, hit is on right side
        if step_x > 0:
            hit_x = hit_x  # Left edge of the tile
        else:
            hit_x = hit_x + TILE_SIZE  # Right edge of the tile

        # Calculate exact y-coordinate using the hit distance
        hit_y = y + perp_wall_dist * ray_dir_y * TILE_SIZE
    else:  # Y-side was hit (horizontal wall)
        # The exact distance to the hit point
        perp_wall_dist = (map_y - y / TILE_SIZE + (1 - step_y) / 2) / ray_dir_y

        # Calculate the exact hit point on the wall
        hit_y = map_y * TILE_SIZE
        # If we're stepping down, hit is on top of new tile; if stepping up, hit is on bottom
        if step_y > 0:
            hit_y = hit_y  # Top edge of the tile
        else:
            hit_y = hit_y + TILE_SIZE  # Bottom edge of the tile

        # Calculate exact x-coordinate using the hit distance
        hit_x = x + perp_wall_dist * ray_dir_x * TILE_SIZE

    return hit_x, hit_y


class OverheadCamera(metaclass=Singleton):
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.target: None | "Player" = None
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

    def update(self) -> None:
        if self.target is None:
            print("No target set for camera")
            return
        self.x = self.target.x - SCREEN_WIDTH // 2
        self.y = self.target.y - SCREEN_HEIGHT // 2


class Camera3d:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def update(self) -> None:
        pass


class Entity:
    @property
    def sx(self) -> float:
        return self.x - self.overhead_camera.x

    @property
    def sy(self) -> float:
        return self.y - self.overhead_camera.y

    def __init__(self, x: float, y: float, w: float, h: float, rot: float) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rot = rot
        self.overhead_camera = OverheadCamera()
        self.game_manager = GameManager()

    def update(self) -> None:
        raise NotImplementedError("Entity subclass must implement update method")

    def draw(self) -> None:
        raise NotImplementedError("Entity subclass must implement draw method")


class Actor(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rot: float,
        speed: float,
        rot_speed: float,
    ) -> None:
        super().__init__(x, y, w, h, rot)
        self.speed = speed
        self.rot_speed = rot_speed
        self.dx = 0
        self.dy = 0
        self.drot = 0

    def delta_forward(self):
        self.dx = self.speed * pyxel.cos(self.rot)
        self.dy = self.speed * pyxel.sin(self.rot)

    def delta_backward(self):
        self.dx = -self.speed * pyxel.cos(self.rot)
        self.dy = -self.speed * pyxel.sin(self.rot)

    def rotate_left(self):
        self.drot = -self.rot_speed

    def rotate_right(self):
        self.drot = self.rot_speed

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.rot += self.drot


class DamageableActor(Actor):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rot: float,
        speed: float,
        rot_speed: float,
        hp: int,
    ) -> None:
        super().__init__(x, y, w, h, rot, speed, rot_speed)
        self.hp = hp

    def take_damage(self, damage: int) -> None:
        self.hp -= damage
        if self.hp <= 0:
            self.on_death()

    def on_death(self) -> None:
        pass


class Player(DamageableActor):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rot: float,
        speed: float = 1,
        rot_speed: float = 0.5,
        hp: int = 100,
    ) -> None:
        super().__init__(x, y, w, h, rot, speed, rot_speed, hp)

    def update(self):
        self.handle_input()
        # Note: Collisions are axis-aligned
        self.x, self.y, self.dx, self.dy = pushback_solid_tile(
            self.x, self.y, self.w, self.h, self.dx, self.dy, 0
        )
        self.move()
        self.reset_movement()

    def reset_movement(self) -> None:
        self.dx = 0
        self.dy = 0
        self.drot = 0

    def handle_input(self):
        if pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.KEY_UP):
            self.delta_forward()
        if pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.KEY_DOWN):
            self.delta_backward()
        if pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.KEY_LEFT):
            self.rotate_left()
        if pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.KEY_RIGHT):
            self.rotate_right()

    def draw(self):
        u, v = PLAYER_MARKER
        u *= TILE_SIZE
        v *= TILE_SIZE
        pyxel.blt(
            self.sx,
            self.sy,
            0,
            u,
            v,
            TILE_SIZE,
            TILE_SIZE,
            COL_TRANSPARENT_BLACK,
            rotate=self.rot + 90,  # Not sure about this +90?
        )


class Raycaster:
    def __init__(self, target: Player, num_rays: int = SCREEN_WIDTH) -> None:
        self.target = target
        self.num_rays = num_rays
        self.deg_increment = RAY_CAST_ARC_DEG / float(self.num_rays)
        self.overhead_camera = OverheadCamera()

    def update(self) -> None:
        rot_start = self.target.rot - RAY_CAST_ARC_DEG * 0.5
        for ri in range(self.num_rays):
            cx, cy = (
                self.target.x + self.target.w // 2,
                self.target.y + self.target.h // 2,
            )
            ray_rot = rot_start + ri * self.deg_increment
            hx, hy = cast_ray(cx, cy, ray_rot)
            # Draw in screen space
            pyxel.line(
                cx - self.overhead_camera.x,
                cy - self.overhead_camera.y,
                hx - self.overhead_camera.x,
                hy - self.overhead_camera.y,
                pyxel.COLOR_GREEN,
            )


class Brownshirt(DamageableActor):
    def __init__(
        self, x: float, y: float, rot: float, speed: float = 1, hp: int = 20
    ) -> None:
        super().__init__(x, y, rot, speed, hp)

    def update(self):
        pass

    def draw(self):
        pass


class Blackshirt(DamageableActor):
    def __init__(
        self, x: float, y: float, rot: float, speed: float = 1, hp: int = 50
    ) -> None:
        super().__init__(x, y, rot, speed, hp)

    def update(self):
        pass

    def draw(self):
        pass


class Powerup(Entity):
    def __init__(self, x: float, y: float, rot: float) -> None:
        super().__init__(x, y, rot)


class HealthPowerup(Powerup):
    def __init__(self, x: float, y: float, rot: float, heal_amount: int) -> None:
        super().__init__(x, y, rot)
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
            title="PyxelStein3D",
            fps=60,
            display_scale=2,
            quit_key=pyxel.KEY_ESCAPE,
        )
        pyxel.load("assets/pyxelstein.pyxres")
        self.overhead_camera = OverheadCamera()
        self.player = Player(
            x=11 * TILE_SIZE,
            y=6 * TILE_SIZE,
            w=TILE_SIZE,
            h=TILE_SIZE,
            rot=0,
            speed=1,
            rot_speed=5,
            hp=100,
        )
        self.overhead_camera.target = self.player
        self.raycaster = Raycaster(target=self.player)
        self.manager = GameManager()
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update()
        self.overhead_camera.update()

    def draw(self):
        pyxel.cls(COL_TRANSPARENT_BLACK)
        # Draw the overhead tilemap
        pyxel.bltm(
            0,
            0,
            0,
            self.overhead_camera.x,
            self.overhead_camera.y,
            self.overhead_camera.w,
            self.overhead_camera.h,
            COL_TRANSPARENT_BLACK,
        )
        self.player.draw()
        self.raycaster.update()


App()
