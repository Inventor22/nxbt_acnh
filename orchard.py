#!/usr/bin/env python3
"""
Animal Crossing Orchard Automation via NXBT (Bluetooth)
Start avatar: bottom-right tree base, facing north.
Press ENTER to begin once you're ready in-game.
"""

import time
import nxbt

# =========================
# TUNABLES
# =========================
# Base move timings
WALK_TILE_S           = 0.60     # straight 1-tile travel when already facing that direction
FACE_ONLY_S           = 0.165     # nudge long enough to change facing, not position
FACE_NUDGE_S          = 0.05     # tiny "face forward" nudge at a tree

# Shake timings
PRESS_A_HOLD_S        = 0.06
AFTER_SHAKE_PAUSE     = 0.20     # animation buffer before anything else
POST_SHAKE_MOVE_DELAY = 2.00     # your requested 2.0s settle before stepping to next tree

# Step-to-next-tree timings when starting FACING NORTH
# (longer than WALK_TILE_S because the avatar rotates + begins moving)
LEFT_STEP_FROM_TREE_S  = 0.70
RIGHT_STEP_FROM_TREE_S = 0.70

# Optional pick-up timings (not used if you’re only shaking right now)
PRESS_Y_HOLD_S        = 0.04
BEFORE_Y_TILE_S       = 0.04
AFTER_Y_TILE_S        = 0.03

TREES_PER_ROW      = 25
TREE_ROWS          = 8
TILE_GAP_BETWEEN   = 1

TILES_BETWEEN_TREES = 1 + TILE_GAP_BETWEEN  # 2 tiles between trunks center-to-center
ROW_BASE_TILES      = ((TREES_PER_ROW - 1) * TILES_BETWEEN_TREES) + 1
COL_BASE_TILES      = ((TREE_ROWS - 1) * TILES_BETWEEN_TREES) + 1

STICK_MAX = 100
UP    = (0,  STICK_MAX)
DOWN  = (0, -STICK_MAX)
LEFT  = (-STICK_MAX, 0)
RIGHT = ( STICK_MAX, 0)

def sleep_s(sec: float):
    if sec > 0:
        time.sleep(sec)

class OrchardBot:
    def __init__(self):
        self.nx = nxbt.Nxbt()
        self.cid = self.nx.create_controller(
            nxbt.PRO_CONTROLLER,
            reconnect_address=self.nx.get_switch_addresses()
        )
        print("Waiting for connection… Put Switch on 'Change Grip/Order' if needed.")
        self.nx.wait_for_connection(self.cid)
        print("Connected. Position your avatar at the bottom-right tree base.")
        input("✅ Press ENTER to start the orchard harvesting automation...")

    # ---------- Low-level inputs ----------
    def press_a(self):
        self.nx.press_buttons(self.cid, [nxbt.Buttons.A], down=PRESS_A_HOLD_S, up=0)

    def press_y(self):
        self.nx.press_buttons(self.cid, [nxbt.Buttons.Y], down=PRESS_Y_HOLD_S, up=0)

    def tilt(self, vec, sec, release=0.05):
        x, y = vec
        self.nx.tilt_stick(self.cid, nxbt.Sticks.LEFT_STICK, x, y, tilted=sec, released=release)

    # ---------- Facing-only nudges (no pixel movement) ----------
    def face_up_only(self):
        self.tilt(UP, FACE_ONLY_S, release=0.00)

    def face_down_only(self):
        self.tilt(DOWN, FACE_ONLY_S, release=0.00)

    def face_left_only(self):
        self.tilt(LEFT, FACE_ONLY_S, release=0.00)

    def face_right_only(self):
        self.tilt(RIGHT, FACE_ONLY_S, release=0.00)

    # ---------- Tile movement ----------
    def move_tiles(self, vec, tiles: int):
        for _ in range(tiles):
            self.tilt(vec, WALK_TILE_S, release=0.00)

    # ---------- Tree interaction ----------
    def nudge_forward_at_tree(self):
        # a tiny forward to ensure we’re 'engaged' with the tree
        self.tilt(UP, FACE_NUDGE_S, release=0.00)

    def shake_current_tree(self):
        self.nudge_forward_at_tree()
        self.press_a()
        sleep_s(AFTER_SHAKE_PAUSE)

    # ---------- Step to adjacent tree when starting FACING NORTH ----------
    def step_left_to_next_tree_from_treeface(self):
        # after-shake settle you asked for
        sleep_s(POST_SHAKE_MOVE_DELAY)
        # move left to the next trunk (timing includes turn+move)
        self.tilt(LEFT, LEFT_STEP_FROM_TREE_S, release=0.06)
        # face north again without advancing
        self.face_up_only()

    def step_right_to_next_tree_from_treeface(self):
        sleep_s(POST_SHAKE_MOVE_DELAY)
        self.tilt(RIGHT, RIGHT_STEP_FROM_TREE_S, release=0.06)
        self.face_up_only()

    # ---------- Full row traversals ----------
    def traverse_row_right_to_left(self):
        # starting at rightmost tree, facing north
        self.shake_current_tree()
        for _ in range(1, TREES_PER_ROW):
            self.step_left_to_next_tree_from_treeface()
            self.shake_current_tree()

    def traverse_row_left_to_right(self):
        # starting at leftmost tree, facing north
        self.shake_current_tree()
        for _ in range(1, TREES_PER_ROW):
            self.step_right_to_next_tree_from_treeface()
            self.shake_current_tree()

    # ---------- Row advances (between rows) ----------
    # After finishing R->L, at LEFTMOST tree, facing north:
    # face left + move 1, face north + move 3, face right + move 1, face north nudge
    def advance_to_next_row_after_R2L(self):
        self.face_left_only()
        self.move_tiles(LEFT, 1)
        self.face_up_only()
        self.move_tiles(UP, 3)
        self.face_right_only()
        self.move_tiles(RIGHT, 1)
        self.face_up_only()

    # After finishing L->R, at RIGHTMOST tree, facing north:
    # face right + move 1, face north + move 3, face left + move 1, face north nudge
    def advance_to_next_row_after_L2R(self):
        self.face_right_only()
        self.move_tiles(RIGHT, 1)
        self.face_up_only()
        self.move_tiles(UP, 3)
        self.face_left_only()
        self.move_tiles(LEFT, 1)
        self.face_up_only()

    # ---------- Phase 1: shake all rows with exact zig-zag ----------
    def phase1_shake_all(self):
        # Row 1 is RIGHT->LEFT from bottom-right start
        go_left = True
        for row in range(TREE_ROWS):
            if go_left:
                self.traverse_row_right_to_left()
            else:
                self.traverse_row_left_to_right()

            if row == TREE_ROWS - 1:
                break  # done after last row

            # advance to next row based on which way we just traversed
            if go_left:
                self.advance_to_next_row_after_R2L()
            else:
                self.advance_to_next_row_after_L2R()

            go_left = not go_left

    def run(self):
        try:
            #self.phase1_shake_all()
            # You can call your Phase 2/3 here after you’re happy with Phase 1 timing.


            self.tilt(UP, 5, release=0.00)

            # t = 2
            # while True:
            #     self.face_up_only()
            #     sleep_s(2)
            #     self.face_left_only()
            #     sleep_s(2)
            #     self.face_down_only()
            #     sleep_s(2)
            #     self.face_right_only()
            #     sleep_s(2)
        finally:
            self.nx.remove_controller(self.cid)
            print("✅ Done. Controller shut down.")

if __name__ == "__main__":
    OrchardBot().run()
