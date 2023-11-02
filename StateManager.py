import logging
import threading
from threading import Thread
from typing import Iterable, Optional

from pygame import display
from pygame import gfxdraw as gfx
from pygame import time
from pygame.color import Color
from pygame.event import Event
from pygame.event import get as get_events
from pygame.font import SysFont
from pygame.surface import Surface


def get_from_set(s:set|Iterable):
    for x in s:return x

# This StateManger takes and passes events

class State:
    manager: "StateManager" = NotImplemented
    @staticmethod
    def exit(to: str, **kwargs)->None:
        """ Call this function to exit the current state to another state """
        raise NotImplementedError("Use a state only with a state manager")
    def on_init(self)->None:
        """ Gets called by the statemanager when the state is initialized the first time
        You can be sure this is called before on_enter is called the first time. """
    def on_enter(self, frm: str, **kwargs)->None:
        """ Gets called by the statemanager when the state is entered. 
        It gets the state its coming from and some optional arguments the other state has passed it """
    def on_exit(self, to: str)->None:
        """ Gets called when the state exits (internally or externally) """
    def update(self, events: list[Event], dt: float)->None:
        """ 
        Your update function that gets called every frame with 
        - the events since the last frame (events)
        - and the time since the last frame (dt)

        If you don't need these attributes define update like so:
        ```python
        def update(self, *_):
            ...
        ```
        """
    def draw(self, s: Surface)->None:
        """ 
        Your draw function that gets called every frame with 
        - the screen to draw on (s)

        """

class LoadingState:
    max_angle = 320
    def __init__(self):
        self.font = SysFont(None,26) #type: ignore
        self.cx,self.cy = display.get_surface().get_rect().center
        self.text = self.font.render("Loading...", True, Color("black"))
        self.text_rect = self.text.get_rect(center=(self.cx,self.cy-100))
        self.angle: float = self.max_angle

    def update(self, dt: float, state_currently_loading: State)->None:
        self.angle -= dt/10
        if self.angle <=10:
            self.angle = self.max_angle

    def draw(self, s:Surface)->None:
        s.blit(self.text,self.text_rect)
        gfx.arc(s,self.cx,self.cy-100,50,0,int(self.angle), Color("black"))

class StateManager:
    def __init__(self,states: dict[str,State],*, start: str="", loading_state: Optional[LoadingState] = None, preload: bool = False):
        assert "" not in states, "\"\" (the empty string) cannot be name of a state"
        self.states = states
        self.loading_state = loading_state or LoadingState()
        self.inited = {k:False for k in self.states.keys()}
        self.loading = {k:False for k in self.states.keys()}
        self.threads: dict[str,Thread] = {}
        for name, state in states.items(): # tell states to which manager they belong
            state.exit = self.set_state #type: ignore
            state.manager = self
            if preload:
                self._init_state(name)
        if len(self.states) == 1:
            print("Why would you only have a single state? It has one upside, we automatically started the StateManager for you. ")
            start = get_from_set(self.states)
        if start:
            self.start(start)
    def __getitem__(self, key: str)->State:
        return self.states[key]

    def start(self, state: str)->"StateManager":
        """ Start the state manager with the given state and return `self`"""
        if not self._current_state:
            assert state in self.states, "Start state has to be in managers states"
            self._current_state = state 
            self._init_state(state)
        return self
    def __call__(self, events: Optional[list[Event]] = None, dt: Optional[float] = None, s: Optional[Surface] = None)->None:
        """ `__calling__` the manager is like updating and drawing at the same time """
        self.update(events, dt)
        self.draw(s)
    def update(self, 
            events: Optional[list[Event]] = None, 
            dt: Optional[float] = None
        )->None:
        """ 
        Update the state manager with given events and delta time 
        If not given it gets from `pygame.event.get` and `pygame.time.get_ticks`
        """
        if not self._current_state:
            raise Exception("StateManager wasn't started yet")
        else:
            # Make sure events are not None
            events = events if events is not None else get_events()
            dt = dt if dt is not None else time.get_ticks()
            if not self.loading[self._current_state]:
                self.current_state().update(events, dt)
            else:
                if self.loading_state is not None:
                    self.loading_state.update(dt, self.current_state())
    def draw(self, s: Optional[Surface])->None:
        """ Draw the state manager to the given `Surface` (default is main display) """
        if not self._current_state:
            raise Exception("StateManager wasn't started yet")
        else:
            # Make sure the surface is not None
            s = s or display.get_surface()
            if not self.loading[self._current_state]:
                self.current_state().draw(s)
            else:
                if self.loading_state is not None:
                    self.loading_state.draw(s)

    _current_state: str = ""
    def current_state(self)->State:
        if self._current_state:
            return self.states[self._current_state]
        else: 
            raise ValueError("Current state not set")
    def current_state_str(self):
        """ The current state as a string"""
        return self._current_state

    def set_state(self, new_state: str, **kwargs):
        if not self._current_state:
            logging.warning("Don't call set_state without starting the StateManager (explicit is better than implicit)")
            self.start(new_state)
        else:
            assert new_state in self.states and new_state,f"State invalid `{new_state}`"
            self._change_state(new_state,kwargs)

    def _init_state(self, state: str)->None:
        if not self.inited[state]:
            self.loading[state] = True
            def thread_func(): # Thread this
                self[state].on_init()
                self.inited[state] = True
                self.loading[state] = False
                del self.threads[threading.current_thread().name]
            thread = Thread(target = thread_func)
            self.threads[thread.name] = thread
            thread.start()
    def _change_state(self, new_state: str, kwargs)->None:
        old_state = self._current_state
        self.loading[new_state] = True
        self._current_state = new_state
        def thread_func():
            self[old_state].on_exit(new_state)
            if not self.inited[new_state]:
                self[new_state].on_init()
                self.inited[new_state] = True
            self[new_state].on_enter(frm = old_state, **kwargs)
            self.loading[new_state] = False
            del self.threads[threading.current_thread().name]
        thread = Thread(target = thread_func)
        self.threads[thread.name] = thread
        thread.start()
            
    def __del__(self):
        for thread in self.threads.values():
            thread.join()
