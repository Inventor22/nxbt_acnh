import time
from random import randint

import nxbt
from nxbt import Buttons
from nxbt import Sticks

def random_colour():

    return [
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
    ]


if __name__ == "__main__":

    # Init NXBT
    nx = nxbt.Nxbt()

    # Get a list of all available Bluetooth adapters
    adapters = nx.get_available_adapters()
    # Prepare a list to store the indexes of the
    # created controllers.
    controller_idxs = []
    # Loop over all Bluetooth adapters and create
    # Switch Pro Controllers
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            nxbt.PRO_CONTROLLER,
            adapter_path=adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    # Select the last controller for input
    controller_idx = controller_idxs[-1]

    # Wait for the switch to connect to the controller
    nx.wait_for_connection(controller_idx)

    # Moving the selected home screen item two spaces to the right and back.
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, 100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, 100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0,
                  tilted=0.25, released=0.25)

    # Return to the "Change Grip/Order Screen"
    nx.press_buttons(controller_idx, [Buttons.A])
    time.sleep(2)
    nx.press_buttons(controller_idx, [Buttons.A])
    time.sleep(2)

    print("Exiting...")
