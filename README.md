# State Manager

A simple pygame state manager with threaded loading using loading screens. 

This means you can use heavy initialization and entry code without having to worry about it. As long as your code needs to finish up, a loading state will be displayed. 

# Set Up

You can choose to install either `pygame` or the community version `pygame-ce`
```shell
pip install pygame
# or
pip install pygame-ce
```

The package is called pgsm (`PyGameStateMachine`)

```shell
pip install pgsm
```

# Usage

You first write the states by inheriting from `State` then you put it all together with the `StateManager`.

Take this as a simple example with a play state and a pause state.

We want to toggle between play and pause state when the user presses "p"

```py
import pygame as pg
from StateManager import State, StateManager

class PlayState(State):
    def on_enter(self):
        print("Playing")

    def update(events, dt):
        # This is an example for handling events
        # and changing states
        for event in events:
            if event.type == pg.KeyDown and event.key == pg.K_p:
                self.exit("pause")

    def draw(self, s):
        """ 
        Whatever you want to draw 
        s is the surface or screen you may draw to
        """

class PauseState(State):
    def on_enter(self, _frm):
        print("Pausing")

    def update(events, dt):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                self.exit("play")

    def draw(self, s):
        """ Whatever you want to draw """

# We use strings as keys to refer to our states
sm = StateManager({
    "play":PlayState(),
    "pause":PauseState()
}, start="play")
```

Now you can use your state machine like this.
The state machine will by default just draw to the main screen. 

```py
SCREEN = pg.display.set_mode((900, 600))

while running:
    dt = clock.tick(60)
    events = pg.event.get()
    for event in events:
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            running = False
        # we could also have done the toggle here
    SCREEN.fill("white")
    sm(events, dt)
    pg.display.flip()
```

The default loading state draws a little spinner. If you want to change how that works, simply override the `LoadingState`.

For example:

```py
from StateManager import LoadingState

class BlankLoadingState(LoadingState):
    def __init__(self, color):
        self.color = color

    def update(self, *args):
        pass

    def draw(self, s):
        s.fill(self.color)
```

And use like this

```py
sm = StateManager({
        "play":PlayState(),
        "pause":PauseState()
    }, 
    start="play", 
    loading_state=BlankLoadingState("black")
)
```

# License

MIT License