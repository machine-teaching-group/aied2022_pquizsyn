from __future__ import annotations
from __future__ import absolute_import
import importlib.util
import inspect
import os
import sys
import traceback as tb
import json
from types import FrameType
from typing import Callable


from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_program import KarelException
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_application import KarelApplication
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_program import KarelProgram
from code.step3_code2task.utils.codeast import json_to_ast
from code.step3_code2task.sym_world import SymWorld


class SymCode:
    """
    This process extracts a module from an arbitary file that contains student code.
    https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    """

    def __init__(self, code_file: str) -> None:
        if not os.path.isfile(code_file):
            raise FileNotFoundError(f"{code_file} could not be found.")

        self.module_name = os.path.basename(code_file)
        if self.module_name.endswith(".py"):
            self.module_name = os.path.splitext(self.module_name)[0]

        spec = importlib.util.spec_from_file_location(
            self.module_name, os.path.abspath(code_file)
        )
        try:
            self.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.mod)  # type: ignore
        except SyntaxError as e:
            # Handle syntax errors and only print location of error
            print(f"Syntax Error: {e}")
            print("\n".join(tb.format_exc(limit=0).split("\n")[1:]))
            sys.exit()

        # Do not proceed if the student has not defined a main function.
        if not hasattr(self.mod, "main"):
            print("Couldn't find the main() function. Are you sure you have one?")
            sys.exit()

    def __repr__(self) -> str:
        return inspect.getsource(self.mod)

    def inject_namespace(self, karel: SymWorld) -> None:
        """
        This function is responsible for doing some Python hackery
        that associates the generic commands the student wrote in their
        file with specific commands relating to the Karel object that exists
        in the world.
        """
        functions_to_override = [
            "move",
            "turn_left",
            "pick_beeper",
            "put_beeper",
            "turn_right",
            # "facing_north",
            # "facing_south",
            # "facing_east",
            # "facing_west",
            # "not_facing_north",
            # "not_facing_south",
            # "not_facing_east",
            # "not_facing_west",
            "front_is_clear",
            "beepers_present",
            "no_beepers_present",
            #"beepers_in_bag",
            #"no_beepers_in_bag",
            "front_is_blocked",
            "left_is_blocked",
            "left_is_clear",
            "right_is_blocked",
            "right_is_clear",
            #"paint_corner",
            #"corner_color_is",
        ]
        for func in functions_to_override:
            setattr(self.mod, func, getattr(karel, func))




class SymApplication():

    def __init__(
        self,
        karel: SymWorld,
        code_file: str,
        json_code_file: str
        # master: tk.Tk,
        # window_width: int = 800,
        # window_height: int = 600,
        # canvas_width: int = 600,
        # canvas_height: int = 400,
    ) -> None:
        # # set window background to contrast white Karel canvas
        # master.configure(background=LIGHT_GREY)
        #
        # # configure location of canvas to expand to fit window resizing
        # master.rowconfigure(0, weight=1)
        # master.columnconfigure(1, weight=1)
        #
        # # set master geometry
        # master.geometry(f"{window_width}x{window_height}")
        #
        # super().__init__(master, background=LIGHT_GREY)

        self.karel = karel
        self.code_file = code_file
        self.json_code_file = json_code_file
        self.num_code_blocks = self.get_num_code_blocks(self.json_code_file)
        #self.world = karel.world
        self.student_code = SymCode(code_file)
        self.student_code.inject_namespace(karel)
        #master.title(self.student_code.module_name)
        if not self.student_code.mod:
            #master.destroy()
            return
        # self.icon = DEFAULT_ICON
        # self.window_width = window_width
        # self.window_height = window_height
        # self.canvas_width = canvas_width
        # self.canvas_height = canvas_height
        # self.master = master
        # self.set_dock_icon()
        self.coverage_info = []
        self.inject_decorator_namespace()
        # self.grid(row=0, column=0)
        # self.create_menubar()
        # self.create_canvas()
        # self.create_buttons()
        # self.create_slider()
        # self.create_status_label()

    def get_num_code_blocks(self, json_file:str):

        try:
            with open(json_file, "r") as fp:
                code_dict = json.load(fp)
        except:
            print("Unable to open the json code file.", json_file)
            exit(0)

        code_ast = json_to_ast(code_dict)
        if code_ast._n_if_only == 0 and code_ast._n_while == 0 and code_ast._n_repeat == 0 and code_ast._n_if_else == 0:
            self.basic_action_flag = True
        else:
            self.basic_action_flag = False
        return code_ast.size()+1 # to include the RUN block



    def karel_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper() -> None:
            # execute Karel function
            karel_fn()
            # redraw canvas with updated state of the world
            #self.canvas.redraw_karel()
            # delay by specified amount
            # sleep(1 - self.speed.get() / 100)

        return wrapper

    def beeper_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper() -> None:
            # execute Karel function
            karel_fn()
            # redraw canvas with updated state of the world
            # self.canvas.redraw_beepers()
            # self.canvas.redraw_karel()
            # delay by specified amount
            # sleep(1 - self.speed.get() / 100)

        return wrapper

    def corner_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper(color: str) -> None:
            # execute Karel function
            karel_fn(color)
            # redraw canvas with updated state of the world
            # self.canvas.redraw_corners()
            # self.canvas.redraw_beepers()
            # self.canvas.redraw_karel()
            # # delay by specified amount
            # sleep(1 - self.speed.get() / 100)

        return wrapper

    def inject_decorator_namespace(self) -> None:
        """
        This function is responsible for doing some Python hackery
        that associates the generic commands the student wrote in their
        file with specific commands relating to the Karel object that exists
        in the world.
        """
        self.student_code.mod.turn_left = self.karel_action_decorator(  # type: ignore
            self.karel.turn_left
        )
        self.student_code.mod.turn_right = self.karel_action_decorator(  # type: ignore
            self.karel.turn_right
        )
        self.student_code.mod.move = self.karel_action_decorator(  # type: ignore
            self.karel.move
        )
        self.student_code.mod.pick_beeper = (  # type: ignore
            self.beeper_action_decorator(self.karel.pick_beeper)
        )
        self.student_code.mod.put_beeper = self.beeper_action_decorator(  # type: ignore
            self.karel.put_beeper
        )
        # self.student_code.mod.paint_corner = (  # type: ignore
        #     self.corner_action_decorator(self.karel.paint_corner)
        # )

    # def disable_buttons(self) -> None:
    #     self.program_control_button.configure(state="disabled")
    #     self.load_world_button.configure(state="disabled")
    #
    # def enable_buttons(self) -> None:
    #     self.program_control_button.configure(state="normal")
    #     self.load_world_button.configure(state="normal")

    def display_error_traceback(self, e: KarelException | NameError) -> None:
        print("Traceback (most recent call last):")
        display_frames: list[tuple[FrameType, int]] = []
        # walk through all the frames in stack trace at time of failure
        for frame, lineno in tb.walk_tb(e.__traceback__):
            frame_info = inspect.getframeinfo(frame)
            # get the name of the file corresponding to the current frame
            filename = frame_info.filename
            # Only display frames generated within the student's code
            if self.student_code.module_name + ".py" in filename:
                display_frames.append((frame, lineno))

        trace = tb.format_list(tb.StackSummary.extract(display_frames))  # type: ignore
        print("".join(trace).strip())
        print(f"{type(e).__name__}: {e}")

    def run_program(self) -> None:
        ### trace the conditions
        # traced_func = trace_conditions(self.student_code.mod.main, return_conditions=True)
        # self.coverage_info = traced_func()
        self.cov = self.student_code.mod.main()




    def run_karel_program(self, input_karel_world: KarelWorld):

        # instance of KarelProgram
        karel_program = KarelProgram("")
        karel_program.world = input_karel_world
        karel_program.avenue, karel_program.street = input_karel_world.karel_start_location[0], input_karel_world.karel_start_location[1]
        karel_program.direction = input_karel_world.karel_start_direction
        karel_program.num_beepers = input_karel_world.karel_start_beeper_count

        # instance of KarelApplication
        karel_app = KarelApplication(karel_program, self.code_file)
        try:
            karel_app.run_program()
        except:
            # print("Error in running concrete Karel Program")
            return None

        return karel_app.karel.karel_seq

    # def reset_world(self) -> None:
    #     self.karel.reset_state()
    #     self.world.reset_world()
    #     self.canvas.redraw_all()
    #     self.status_label.configure(text="Reset to initial state.", fg="black")
    #     # Once world has been reset, program control button resets to "run" mode
    #     self.program_control_button["text"] = "Run Program"
    #     self.program_control_button["command"] = self.run_program
    #     self.update()
    #
    # def load_world(self) -> None:
    #     default_worlds_path = os.path.join(os.path.dirname(__file__), "worlds")
    #     filename = askopenfilename(
    #         initialdir=default_worlds_path,
    #         title="Select Karel World",
    #         filetypes=[("Karel Worlds", "*.w")],
    #         parent=self.master,
    #     )
    #     # User hit cancel and did not select file, so leave world as-is
    #     if filename == "":
    #         return
    #     self.world.reload_world(filename=filename)
    #     self.karel.reset_state()
    #     # self.canvas.redraw_all()
    #     # # Reset speed slider
    #     # self.scale.set(self.world.init_speed)
    #     # self.status_label.configure(
    #     #     text=f"Loaded world from {os.path.basename(filename)}.", fg="black"
    #     # )
    #
    #     # # Make sure program control button is set to 'run' mode
    #     # self.program_control_button["text"] = "Run Program"
    #     # self.program_control_button["command"] = self.run_program
