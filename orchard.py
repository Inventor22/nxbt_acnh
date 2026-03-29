#!/usr/bin/env python3
"""
ACNH Orchard: per-tree shake & immediate pickup via NXBT (Bluetooth)

Start: bottom-right tree, stand one tile to its RIGHT, facing LEFT.
Flow:
  - Row 1: move LEFT across 25 trees, per-tree: A, pick 3 fruits using gap tiles
  - Row-advance (LEFT 1, UP 3, RIGHT 1)
  - Row 2: move RIGHT across 25 trees (mirrored pattern)
  - Repeat for 8 rows total (zig-zag)
"""

import time
import nxbt

# =========================
# TUNABLES (seconds)
# =========================
WALK_TILE_S       = 0.275   # exact time to walk ONE in-game tile. Tune this first.
A_HOLD_S          = 0.08   # hold for shake
Y_HOLD_S          = 0.05   # hold to pick up
SETTLE_S          = 1.06   # tiny pause after moves or presses
FACE_NUDGE_S      = 0.16   # micro-nudge to “lock” facing before A

# Orchard geometry
TREES_PER_ROW     = 25
TREE_ROWS         = 8
# Between-row offset: with one empty tile between tree rows → 3 tiles up to reach next row’s baseline
ROW_UP_TILES      = 3

# =========================
# STICK VECTORS (NXBT: [-100,100])
# =========================
MAX = 100
UP    = (0,  MAX)
DOWN  = (0, -MAX)
LEFT  = (-MAX, 0)
RIGHT = ( MAX, 0)

def sleep_s(s):
    if s > 0:
        time.sleep(s)

class OrchardPerTree:
    def __init__(self):
        self.nx = nxbt.Nxbt()
        self.cid = self.nx.create_controller(nxbt.PRO_CONTROLLER,
                                             reconnect_address=self.nx.get_switch_addresses())
        print("Open 'Change Grip/Order' on the Switch if not already paired…")
        self.nx.wait_for_connection(self.cid)
        print("Connected. Place avatar at the RIGHT of the bottom-right tree, facing LEFT.")
        input("Press ENTER to start…")

    # ---- low-level helpers ----
    def move(self, vec, seconds):
        x, y = vec
        self.nx.tilt_stick(self.cid, nxbt.Sticks.LEFT_STICK, x, y, tilted=seconds, released=0)

    def move_tiles(self, vec, tiles):
        for _ in range(tiles):
            self.move(vec, WALK_TILE_S)

    def face(self, vec):
        # Small nudge to set facing without significant displacement
        self.move(vec, FACE_NUDGE_S)

    def press_a(self):
        self.nx.press_buttons(self.cid, [nxbt.Buttons.A])

    def press_y(self):
        self.nx.press_buttons(self.cid, [nxbt.Buttons.Y])

    # ---- per-tree patterns ----
    def tree_cycle_leftward(self):
        """
        Preconditions:
          - Standing ONE TILE to the RIGHT of current tree, facing LEFT.
        Steps (your new plan):
          1) Face left & shake (A). 3 fruits fall: left, down, right; we’re on the RIGHT fruit.
          2) Pick Y (right fruit).
          3) Move DOWN 1.
          4) Move LEFT 2 → stand on second fruit; pick Y.
          5) Move LEFT 1, then UP 1 → stand on third fruit; pick Y.
          6) Re-align to the RIGHT of the NEXT tree to the left: move RIGHT 1; face LEFT.
             (Net effect per-tree: advances to the next tree’s start position.)
        """
        # 1) shake
        self.press_a()
        sleep_s(1.5)

        # 2) pick right fruit (we already stand on it)
        self.press_y()
        sleep_s(0.5)

        # 3) down 1
        self.face(DOWN)
        self.move_tiles(DOWN, 1)

        # 4) left 1 → second fruit; pick
        self.face(LEFT)
        self.move_tiles(LEFT, 1)
        self.press_y()
        sleep_s(0.5)

        # 5) left 1, up 1 → third fruit; pick
        self.move_tiles(LEFT, 1)
        self.face(UP)
        self.move_tiles(UP, 1)
        self.press_y()
        sleep_s(0.5)

        # 6) align for NEXT tree to the left
        self.face(LEFT)

    def tree_cycle_rightward(self):
        """
        Mirror of leftward cycle.
        Preconditions:
          - Standing ONE TILE to the LEFT of current tree, facing RIGHT.
        Mirror steps:
          1) Face right & shake (A). We’re on the LEFT fruit.
          2) Pick Y (left fruit).
          3) Move DOWN 1.
          4) Move RIGHT 2 → second fruit; pick Y.
          5) Move RIGHT 1, then UP 1 → third fruit; pick Y.
          6) Align to the LEFT of the NEXT tree to the right: move LEFT 1; face RIGHT.
        """
        self.face(RIGHT)
        self.press_a()

        self.press_y()

        self.move_tiles(DOWN, 1)

        self.move_tiles(RIGHT, 2)
        self.press_y()

        self.move_tiles(RIGHT, 1)
        self.move_tiles(UP, 1)
        self.press_y()

        self.move_tiles(LEFT, 1)
        self.face(RIGHT)

    # ---- row logic ----
    def row_leftward(self):
        # At row start: to the RIGHT of first tree in this row, facing LEFT.
        for i in range(TREES_PER_ROW):
            self.tree_cycle_leftward()

    def row_rightward(self):
        # At row start: to the LEFT of first tree in this row, facing RIGHT.
        for i in range(TREES_PER_ROW):
            self.tree_cycle_rightward()

    def row_advance_from_left_edge(self):
        # When you end a leftward row: you’re on the far LEFT.
        # As before: LEFT 1, UP 3, RIGHT 1.
        self.move_tiles(LEFT, 1)
        self.move_tiles(UP, ROW_UP_TILES)
        self.move_tiles(RIGHT, 1)
        # After this, for the next row (which is rightward),
        # you should be one tile LEFT of the first tree, facing RIGHT.
        self.face(RIGHT)

    def row_advance_from_right_edge(self):
        # When you end a rightward row: you’re on the far RIGHT.
        # As before: RIGHT 1, UP 3, LEFT 1.
        self.move_tiles(RIGHT, 1)
        self.move_tiles(UP, ROW_UP_TILES)
        self.move_tiles(LEFT, 1)
        # Prepare facing LEFT for the next row.
        self.face(LEFT)

    def run(self):
        try:
            # Row 1: LEFTWARD (we start at right of the bottom-right tree)
            self.row_leftward()

            for r in range(1, TREE_ROWS):
                if r % 2 == 1:
                    # Just finished a LEFTWARD row (at left edge) → advance then go RIGHTWARD
                    self.row_advance_from_left_edge()
                    self.row_rightward()
                else:
                    # Just finished a RIGHTWARD row (at right edge) → advance then go LEFTWARD
                    self.row_advance_from_right_edge()
                    self.row_leftward()

            print("✅ Finished all rows.")
        finally:
            self.nx.remove_controller(self.cid)
            print("Controller shut down.")

if __name__ == "__main__":
    OrchardPerTree().run()
