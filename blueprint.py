import cv2
import json
import base64
import zlib
import copy
import pyperclip
import math

class BluePrint(object):
    """
    蓝图生成
    """

    BP_MAIN = {
        "blueprint": {
            "icons": [
            {
                "signal": {"name": "decider-combinator"},
                "index": 1
            }
            ],
            "entities": [],
            "wires": [],
            "item": "blueprint",
            "version": 562949954732035
        }
    }

    BP_LAMP = {
        "entity_number": 1,
        "name": "small-lamp",
        "position": {
            "x": 26.5,
            "y": -108.5
        },
        "control_behavior": {
            "use_colors": True,
            "color_mode": 1
        },
        "color": {
            "r": 0,
            "g": 0,
            "b": 0,
            "a": 1
        },
        "always_on": True
    }

    BP_CONSTANT_COMBINATOR = {
        "entity_number": 1,
        "name": "constant-combinator",
        "position": {
            "x": 26.5,
            "y": -108.5
        },
        "control_behavior": {
            "sections": {
                "sections": [
                    {
                        "index": 1,
                        "filters": [
                            {
                                "index": 1,
                                "type": "virtual",
                                "name": "signal-A",
                                "quality": "normal",
                                "comparator": "=",
                                "count": 100
                            }
                        ]
                    }
                ]
            }
        }
    }

    BP_DECIDER_COMBINATOR = {
        "entity_number": 1,
        "name": "decider-combinator",
        "position": {
            "x": 34.5,
            "y": -103
        },
        "control_behavior": {
            "decider_conditions": {
                "conditions": [
                    {
                        "first_signal": {
                            "type": "virtual",
                            "name": "signal-heart"
                        },
                        "constant": 1,
                        "comparator": "=",
                        "first_signal_networks": {
                            "red": True,
                            "green": False
                        }
                    }
                ],
                "outputs": [
                    {
                        "signal": {
                            "type": "virtual",
                            "name": "signal-everything"
                        },
                        "networks": {
                            "red": False,
                            "green": True
                        }
                    }
                ]
            }
        }
    }

    BP_ARITHMETIC_COMBINATOR = {
        "entity_number": 1,
        "name": "arithmetic-combinator",
        "position": {
            "x": 25.5,
            "y": -108
        },
        "control_behavior": {
            "arithmetic_conditions": {
                "first_signal": {
                    "type": "virtual",
                    "name": "signal-A"
                },
                "second_constant": 255,
                "operation": "AND",
                "output_signal": {
                    "type": "virtual",
                    "name": "signal-red"
                }
            }
        }
    }

    def __init__(self, film_path):
        # if you want to change the height, make sure the sig_pool has enough signals
        # all signals type should be virtual in the pool
        # signals count >= height / 4
        self.HEIGHT = 100
        self.SIG_POOL = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
                        "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"]
        self.MODULE_DISTANCE = 10
        self.DISK_LAYER_SIZE = 500  # frame count for each storage layer
        self.DISK_LAYER_DISTANCE = 5
        self.film_path = film_path
        self.cap = cv2.VideoCapture(self.film_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if self.frame_count < 1 or width < 1 or height < 1:
            print("ERROR, read video failed!")
            exit(0)
        self.WIDTH = int(self.HEIGHT * 1.0 / height * width)
        self.clock_signal = "signal-heart"  # if first_signal_networks is filtered, could equal to signal in sig_pool
        self.blueprint = None
        self.cover_frame_before_index = 1
        self.cover_frame_after_index = self.frame_count
        self.show_cover_before = True
        self.show_cover_after = True
        self.cover_frame_before = None  # cv.Mat, cover frame
        self.cover_frame_after = None  # cv.Mat, cover frame after the film
    
    def set_film_cover(self, frame_before_index=-1, frame_after_index=-1,
                     picture_before_path="", picture_after_path="",
                     show_before=True, show_after=True):
        """
        set film cover, default cover is the first frame
        frame index: which frame to use as cover, start from 1, default is first and last frame
        picture path: path of the picture to use as cover
        show: show the cover or not
        if both frame index and picture path are set, picture path will be used rather than frame index
        if no valid cover is set but show is True, the default indexed frame will be used as cover
        """
        if frame_before_index == -1:
            frame_before_index = 1
        if frame_after_index == -1:
            frame_after_index = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.cover_frame_before_index = frame_before_index
        self.cover_frame_after_index = frame_after_index
        if self.cover_frame_before_index > int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or self.cover_frame_before_index < 1:
            print("ERROR, cover before frame index out of range!")
            self.cover_frame_before_index = 1
        if self.cover_frame_after_index > int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or self.cover_frame_after_index < 1:
            print("ERROR, cover after frame index out of range!")
            self.cover_frame_after_index = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.show_cover_before = show_before
        self.show_cover_after = show_after
        if picture_before_path:
            self.cover_frame_before = cv2.imread(picture_before_path, cv2.IMREAD_COLOR)
            if self.cover_frame_before is None or not self.cover_frame_before.data:
                self.cover_frame_before = None
                print("ERROR, read cover before picture failed!")
        if picture_after_path:
            self.cover_frame_after = cv2.imread(picture_after_path, cv2.IMREAD_COLOR)
            if self.cover_frame_after is None or not self.cover_frame_after.data:
                self.cover_frame_after = None
                print("ERROR, read cover after picture failed!")

    def encode(self, ss):
        """ss is a bytes object of json string, return blueprint used in game"""
        return '0' + str(base64.b64encode(zlib.compress(ss, 9)), encoding='utf8')

    def build_lamp(self):
        index = 1
        x_pos = 0
        y_pos = 0
        entities = self.blueprint["blueprint"]["entities"]
        for col in range(self.WIDTH):
            for row in range(self.HEIGHT):
                lamp = copy.deepcopy(BluePrint.BP_LAMP)
                lamp["entity_number"] = index
                lamp["position"] = {"x": x_pos, "y": y_pos}
                index += 1
                y_pos += 1
                entities.append(lamp)
            x_pos += 1
            y_pos = 0

    def build_decoder(self):
        index = self.HEIGHT * self.WIDTH + 1
        x_pos = 0
        entities = self.blueprint["blueprint"]["entities"]
        for col in range(self.WIDTH):
            y_pos = self.HEIGHT + self.MODULE_DISTANCE  # leave some space after lamps
            # 4 bytes per signal, 1 lamp per byte => 1 signal can store 4 lamp color
            for i in range(math.ceil(self.HEIGHT / 4)):
                signal = "signal-" + self.SIG_POOL[i]
                shift=24
                for B in range(4):
                    right_shift = B < 3
                    op = ">>" if right_shift else "<<"
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        "signal-each", "signal-each", "/", 0xE0))
                    index += 1
                    y_pos += 2
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        "signal-each", "signal-each", "*", 0xFF))
                    self.connect(index - 1, 2, index, 4)
                    index += 1
                    y_pos += 2
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        "signal-red", "signal-red", "AND", 0xE0))
                    self.connect(index - 1, 2, index, 4)
                    index += 1
                    y_pos += 2
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        signal, "signal-red", op, shift))
                    if B != 0 or i != 0:
                        self.connect(index - 4, 1, index, 1)
                    self.connect(index - 1, 1, index, 3)
                    index += 1
                    y_pos += 2
                    shift = shift - 3 if right_shift else shift + 3
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        "signal-green", "signal-green", "AND", 0xE0))
                    self.connect(index - 2, 4, index, 4)
                    index += 1
                    y_pos += 2
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos, signal,
                        "signal-green", op, shift))
                    self.connect(index - 2, 1, index, 1)
                    self.connect(index - 1, 1, index, 3)
                    index += 1
                    y_pos += 2
                    shift = shift - 3 if right_shift else shift + 3
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos,
                        "signal-blue", "signal-blue", "AND", 0xC0))
                    self.connect(index - 2, 4, index, 4)
                    index += 1
                    y_pos += 2
                    entities.append(self.get_arithmetic_combinator(index, x_pos, y_pos, signal,
                        "signal-blue", op, shift))
                    self.connect(index - 2, 1, index, 1)
                    self.connect(index - 1, 1, index, 3)
                    shift = shift - 2 if right_shift else shift + 2
                    index += 1
                    y_pos += 2
            x_pos += 1

    def build_storage(self):
        # 1 lamp, 6 arithmetic combinator for color extraction, 2 arithmetic combinator for lerp
        index = self.HEIGHT * self.WIDTH * 9 + 1
        x_pos_start = self.WIDTH + self.MODULE_DISTANCE
        y_pos_start = self.HEIGHT + self.MODULE_DISTANCE + 2 * 3 + 1
        entities = self.blueprint["blueprint"]["entities"]
        frame_idx = 0
        frame_delay = 300  # make time to close the signal combinator for watch film
        # processing status, -1 for done
        # 1 for film content, 2 for cover before, 3 for cover after
        stage = 1
        while stage > 0:
            if stage == 1:  # film content
                ret, original_frame = self.cap.read()
                if not ret:
                    stage = 2  # no more film content, process cover now
                    if not self.show_cover_before:
                        continue
                    if self.cover_frame_before is not None:
                        original_frame = self.cover_frame_before
            elif stage == 2:  # cover before has been processed
                stage = 3  # process cover after now
                if not self.show_cover_after:
                    continue
                if self.cover_frame_after is not None:
                    original_frame = self.cover_frame_after
            elif stage == 3:  # cover after has been processed
                stage = -1  # all process done
                break

            first_line = frame_idx % self.DISK_LAYER_SIZE == 0
            first_layer = frame_idx < self.DISK_LAYER_SIZE
            if first_line:
                x_pos_start = (self.WIDTH + self.MODULE_DISTANCE
                    + (self.WIDTH + self.DISK_LAYER_DISTANCE) * (frame_idx // self.DISK_LAYER_SIZE))
                x_pos = x_pos_start
                y_pos = y_pos_start
            if stage == 1:
                frame_idx += 1
            frame = cv2.resize(original_frame, (self.WIDTH, self.HEIGHT))
            if frame_idx == self.cover_frame_before_index and self.cover_frame_before is None:
                self.cover_frame_before = frame
            if frame_idx == self.cover_frame_after_index and self.cover_frame_after is None:
                self.cover_frame_after = frame
            arr = self.frame_to_array(frame)
            for col in range(self.WIDTH):
                if stage == 2:
                    dc = self.get_decider_combinator(index, x_pos, y_pos, self.clock_signal, "<", 1 + frame_delay)
                elif stage == 3:
                    dc = self.get_decider_combinator(index, x_pos, y_pos, self.clock_signal, ">", frame_idx + frame_delay)
                else:
                    dc = self.get_decider_combinator(index, x_pos, y_pos, self.clock_signal, "=", frame_idx + frame_delay)     
                entities.append(dc)
                if first_line:
                    if not first_layer:
                        self.connect(index - self.WIDTH * 2 * self.DISK_LAYER_SIZE, 3, index, 3)  # storage output
                    if col != 0:
                        self.connect(index - 2, 2, index, 2)  # clock signal
                    elif frame_idx != 1:
                        self.connect(index - self.WIDTH * 2 * self.DISK_LAYER_SIZE, 2, index, 2)
                else:
                    self.connect(index - self.WIDTH * 2, 2, index, 2)  # clock signal
                    self.connect(index - self.WIDTH * 2, 3, index, 3)  # storage output
                index += 1
                y_pos += 1.5
                entities.append(self.get_constant_combinator(index, x_pos, y_pos, arr[col]))
                self.connect(index - 1, 1, index, 1)
                index += 1
                x_pos += 1
                y_pos -= 1.5
            x_pos = x_pos_start
            y_pos += 3
            print("\rloading frame {:04}/{:04}".format(frame_idx, self.frame_count), end="")
        print("\n", end="")

    def build_clock(self):
        index = (self.HEIGHT * self.WIDTH * 9
            + self.WIDTH * 2 * (self.frame_count + int(self.show_cover_before) + int(self.show_cover_after))
            + 1)
        x_pos = self.WIDTH + self.MODULE_DISTANCE
        y_pos = self.HEIGHT + self.MODULE_DISTANCE - 10
        entities = self.blueprint["blueprint"]["entities"]
        cc = {
            "entity_number": index,
            "name": "constant-combinator",
            "position": {"x": x_pos, "y": y_pos},
            "direction": 8,
            "control_behavior": {
                "sections": {
                    "sections": [
                        {
                            "index": 1,
                            "filters": [
                                {
                                    "index": 1,
                                    "type": "virtual",
                                    "name": self.clock_signal,
                                    "quality": "normal",
                                    "comparator": "=",
                                    "count": 1
                                }
                            ]
                        }
                    ]
                },
                "is_on": False
            }
        }
        entities.append(cc)
        index += 1
        y_pos += 1.5
        ac = self.get_arithmetic_combinator(index, x_pos, y_pos,
            self.clock_signal, self.clock_signal, "+", 0)
        ac["direction"] = 8
        entities.append(ac)
        self.connect(index - 1, 2, index, 2)
        self.connect(index, 1, index, 3)
        index += 1
        y_pos += 2
        ac = self.get_arithmetic_combinator(index, x_pos, y_pos,
            self.clock_signal, self.clock_signal, "/", 1)
        ac["direction"] = 8
        entities.append(ac)
        self.connect(index - 1, 4, index, 2)

    def link(self):
        """
        add wires between modules
        """
        # link lamp and decoder
        idx_decoder_start = self.HEIGHT * self.WIDTH + 1
        idx_decoder = idx_decoder_start
        for idx_lamp in range(1, idx_decoder_start):
            self.connect(idx_lamp, 2, idx_decoder, 4)
            idx_decoder += 8  # 8 decider combinator light a lamp

        # link decoder and storage
        idx_decoder = idx_decoder_start + 3
        idx_storage = self.HEIGHT * self.WIDTH * 9 + 1
        for i in range(self.WIDTH):
            self.connect(idx_decoder, 1, idx_storage, 3)
            idx_decoder += self.HEIGHT * 8
            idx_storage += 2

        # link storage and clock
        idx_storage = self.HEIGHT * self.WIDTH * 9 + 1
        idx_clock = (idx_storage
            + self.WIDTH * 2 * (self.frame_count + int(self.show_cover_before) + int(self.show_cover_after))
            + 2)
        self.connect(idx_storage, 2, idx_clock, 4)

    # interface
    def get_player(self):
        print("generate player")
        self.blueprint = copy.deepcopy(BluePrint.BP_MAIN)
        self.build_lamp()
        self.build_decoder()
        self.build_storage()
        self.build_clock()
        self.link()
        print("generate blueprint string")
        s = self.encode(json.dumps(self.blueprint).encode())
        # s = json.dumps(self.blueprint)
        pyperclip.copy(s)
        print("blueprint has copied to clipboard")
        return s

    @staticmethod
    def get_arithmetic_combinator(index, x_pos, y_pos, sig_in, sig_out, op, constant_nu):
        return {
            "entity_number": index, # 1,
            "name": "arithmetic-combinator",
            "position": {
                "x": x_pos, # 25.5,
                "y": y_pos # -108
            },
            "control_behavior": {
                "arithmetic_conditions": {
                    "first_signal": {
                        "type": "virtual",
                        "name": sig_in  # "signal-A"
                    },
                    "second_constant": constant_nu,  # 255
                    "operation": op,  # "AND", "<<", ">>"
                    "output_signal": {
                        "type": "virtual",
                        "name": sig_out  # "signal-red"
                    }
                }
            }
        }
    
    @staticmethod
    def get_decider_combinator(index, x_pos, y_pos, sig_in, op, constant_nu):
        return {
            "entity_number": index,
            "name": "decider-combinator",
            "position": {
                "x": x_pos,
                "y": y_pos
            },
            "control_behavior": {
                "decider_conditions": {
                    "conditions": [
                        {
                            "first_signal": {
                                "type": "virtual",
                                "name": sig_in
                            },
                            "constant": constant_nu,
                            "comparator": op,
                            "first_signal_networks": {
                                "red": False,
                                "green": True
                            }
                        }
                    ],
                    "outputs": [
                        {
                            "signal": {
                                "type": "virtual",
                                "name": "signal-everything"
                            },
                            "networks": {
                                "red": True,
                                "green": False
                            }
                        }
                    ]
                }
            }
        }

    def get_constant_combinator(self, index, x_pos, y_pos, sig_values):
        combinator = {
            "entity_number": index,
            "name": "constant-combinator",
            "position": {
                "x": x_pos,
                "y": y_pos
            },
            "control_behavior": {
                "sections": {
                    "sections": [
                        {
                            "index": 1,
                            "filters": []
                        }
                    ]
                }
            }
        }

        for i in range(len(self.SIG_POOL)):
            if i >= len(sig_values):
                break
            combinator["control_behavior"]["sections"]["sections"][0]["filters"].append({
                "index": i + 1,
                "type": "virtual",
                "name": "signal-" + self.SIG_POOL[i],
                "quality": "normal",
                "comparator": "=",
                "count": sig_values[i]
            })
        return combinator

    def connect(self, entity_a, pole_a, entitiy_b, pole_b):
        self.blueprint["blueprint"]["wires"].append([entity_a, pole_a, entitiy_b, pole_b])

    @staticmethod
    def R8G8B8_to_R3G3B2(R, G, B):
        return (R & 0b11100000) | ((G & 0b11100000) >> 3) | ((B & 0b11000000) >> 6)
    
    @staticmethod
    def R3G3B2_to_R8G8B8(RGB, seperated=False):
        """you may want to use this function to view the effect of color compression"""
        if seperated:
            return RGB & 0b11100000, (RGB & 0b00011100) << 3, (RGB & 0b00000011) << 6
        return ((RGB & 0b11100000) << 16 ) | ((RGB & 0b00011100) << 8) | (RGB & 0b00000011)

    def frame_to_array(self, frame):
        """
        col major, frame size is self.WIDTH * self.HEIGHT
        process frame pixels from top to bottom, left to right
        1 pixel data is stored in 3 bytes with format R8G8B8, compress it to 1 byte with format R3G3B2
        pack 4 pixels to 1 int with 4 bytes
        |    value0     |     value1    | ...
        px0 px1 px2 px3  px4 px5 px6 px7  px8 px9 ...
        return format: [[col0],[col1],[col2]]
        """
        ret = []
        for col in range(self.WIDTH):
            arr = []
            row = 0
            while row < self.HEIGHT:
                value = 0
                for idx in range(4):
                    value <<= 8
                    b, g, r = frame[row, col]
                    value |= self.R8G8B8_to_R3G3B2(int(r), int(g), int(b))
                    row += 1
                if value > 0x7FFFFFFF:  # python cannot overflow, make sure value is 32 bit signed int
                    value = int.from_bytes(value.to_bytes(4, signed=False), signed=True)
                arr.append(value)
            ret.append(arr)
        return ret

def main():
    x = BluePrint("res/eva.mp4")
    x.set_film_cover(picture_before_path="res/fireworks.jpeg",
                    frame_after_index=-1, show_before=True, show_after=True)
    x.get_player()

if __name__ == "__main__":
    main()
