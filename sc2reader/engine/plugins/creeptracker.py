# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from io import BytesIO

try:
    from sets import Set
except ImportError:
    Set = set
try:
    # required for CreepTracker, but CreepTracker is optional
    from PIL.Image import open as PIL_open
    from PIL.Image import ANTIALIAS
except ImportError:
    pass
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from collections import defaultdict
from itertools import tee

# The creep tracker plugin
class CreepTracker(object):
    """
    The Creep tracker populates player.max_creep_spread and
    player.creep_spread by minute
    This uses the creep_tracker class to calculate the features
    """

    name = "CreepTracker"

    def handleInitGame(self, event, replay):
        try:
            if len(replay.tracker_events) == 0:
                return
            if replay.map is None:
                replay.load_map()
            self.creepTracker = creep_tracker(replay)
            for player in replay.players:
                if player.play_race[0] == "Z":
                    self.creepTracker.init_cgu_lists(player.pid)
        except Exception as e:
            print("Whoa! {}".format(e))
            pass

    def handleUnitDiedEvent(self, event, replay):
        try:
            self.creepTracker.remove_from_list(event.unit_id, event.second)
        except Exception as e:
            print("Whoa! {}".format(e))
            pass

    def handleUnitInitEvent(self, event, replay):
        try:
            if event.unit_type_name in ["CreepTumor", "Hatchery", "NydusCanal"]:
                self.creepTracker.add_to_list(
                    event.control_pid,
                    event.unit_id,
                    (event.x, event.y),
                    event.unit_type_name,
                    event.second,
                )
        except Exception as e:
            print("Whoa! {}".format(e))
            pass

    def handleUnitBornEvent(self, event, replay):
        try:
            if event.unit_type_name == "Hatchery":
                self.creepTracker.add_to_list(
                    event.control_pid,
                    event.unit_id,
                    (event.x, event.y),
                    event.unit_type_name,
                    event.second,
                )
        except Exception as e:
            print("Whoa! {}".format(e))
            pass

    def handleEndGame(self, event, replay):
        try:
            if len(replay.tracker_events) == 0:
                return
            for player in replay.players:
                if player.play_race[0] == "Z":
                    self.creepTracker.reduce_cgu_per_minute(player.pid)
                    player.creep_spread_by_minute = (
                        self.creepTracker.get_creep_spread_area(player.pid)
                    )
                    # note that player.max_creep_spread may be a tuple or an int
                    if player.creep_spread_by_minute:
                        player.max_creep_spread = max(
                            player.creep_spread_by_minute.items(), key=lambda x: x[1]
                        )
                    else:
                        ## Else statement is for players with no creep spread(ie: not Zerg)
                        player.max_creep_spread = 0
        except Exception as e:
            print("Whoa! {}".format(e))
            pass


## The class used to used to calculate the creep spread
class creep_tracker:
    def __init__(self, replay):
        # if the debug option is selected, minimaps will be printed to a file
        ##and a stringIO containing the minimap image will be saved for
        ##every minite in the game and the minimap with creep highlighted
        ## will be printed out.
        self.debug = replay.opt["debug"]
        ##This list contains creep spread area for each player
        self.creep_spread_by_minute = dict()
        ## this list contains a minimap highlighted with creep spread for each player
        if self.debug:
            self.creep_spread_image_by_minute = dict()
        ## This list contains all the active cgus in every time frame
        self.creep_gen_units = dict()
        ## This list corresponds to creep_gen_units storing the time of each CGU
        self.creep_gen_units_times = dict()
        ## convert all possible cgu radii into a sets of coordinates centred around the origin,
        ## in order to use this with the CGUs, the centre point will be
        ## subtracted with coordinates of cgus created in game
        self.unit_name_to_radius = {"CreepTumor": 10, "Hatchery": 8, "NydusCanal": 5}
        self.radius_to_coordinates = dict()
        for x in self.unit_name_to_radius:
            self.radius_to_coordinates[
                self.unit_name_to_radius[x]
            ] = self.radius_to_map_positions(self.unit_name_to_radius[x])
        # Get map information
        replayMap = replay.map
        # extract image from replay package
        mapsio = BytesIO(replayMap.minimap)
        im = PIL_open(mapsio)
        ##remove black box around minimap

        # https://github.com/jonomon/sc2reader/commit/2a793475c0358989e7fda4a75642035a810e2274
        #        cropped = im.crop(im.getbbox())
        #        cropsize = cropped.size

        cropsizeX = replay.map.map_info.camera_right - replay.map.map_info.camera_left
        cropsizeY = replay.map.map_info.camera_top - replay.map.map_info.camera_bottom
        cropsize = (cropsizeX, cropsizeY)

        self.map_height = 100.0
        # resize height to MAPHEIGHT, and compute new width that
        # would preserve aspect ratio
        self.map_width = int(cropsize[0] * (float(self.map_height) / cropsize[1]))
        self.mapSize = self.map_height * self.map_width

        ## the following parameters are only needed if minimaps have to be printed
        #        minimapSize = ( self.map_width,int(self.map_height) )
        #        self.minimap_image = cropped.resize(minimapSize, ANTIALIAS)

        mapOffsetX = replayMap.map_info.camera_left
        mapOffsetY = replayMap.map_info.camera_bottom
        mapCenter = [mapOffsetX + cropsize[0] / 2.0, mapOffsetY + cropsize[1] / 2.0]
        # this is the center of the minimap image, in pixel coordinates
        imageCenter = [(self.map_width / 2), self.map_height / 2]
        # this is the scaling factor to go from the SC2 coordinate
        # system to pixel coordinates
        self.image_scale = float(self.map_height) / cropsize[1]
        self.transX = imageCenter[0] + self.image_scale * (mapCenter[0])
        self.transY = imageCenter[1] + self.image_scale * (mapCenter[1])

    def radius_to_map_positions(self, radius):
        ## this function converts all radius into map coordinates
        ## centred around  the origin that the creep can exist
        ## the cgu_radius_to_map_position function will simply
        ## subtract every coordinate with the centre point of the tumour
        output_coordinates = list()
        # Sample a square area using the radius
        for x in range(-radius, radius):
            for y in range(-radius, radius):
                if (x ** 2 + y ** 2) <= (radius * radius):
                    output_coordinates.append((x, y))
        return output_coordinates

    def init_cgu_lists(self, player_id):
        self.creep_spread_by_minute[player_id] = defaultdict(int)
        if self.debug:
            self.creep_spread_image_by_minute[player_id] = defaultdict(StringIO)
        self.creep_gen_units[player_id] = list()
        self.creep_gen_units_times[player_id] = list()

    def add_to_list(self, player_id, unit_id, unit_location, unit_type, event_time):
        # This functions adds a new time frame to creep_generating_units_list
        # Each time frame contains a list of all CGUs that are alive
        length_cgu_list = len(self.creep_gen_units[player_id])
        if length_cgu_list == 0:
            self.creep_gen_units[player_id].append(
                [(unit_id, unit_location, unit_type)]
            )
            self.creep_gen_units_times[player_id].append(event_time)
        else:
            # if the list is not empty, take the previous time frame,
            # add the new CGU to it and append it as a new time frame
            previous_list = self.creep_gen_units[player_id][length_cgu_list - 1][:]
            previous_list.append((unit_id, unit_location, unit_type))
            self.creep_gen_units[player_id].append(previous_list)
            self.creep_gen_units_times[player_id].append(event_time)

    def remove_from_list(self, unit_id, time_frame):
        ## This function searches is given a unit ID for every unit who died
        ## the unit id will be searched in cgu_gen_units for matches
        ## if there are any, that unit will be removed from active CGUs
        ## and appended as a new time frame
        for player_id in self.creep_gen_units:
            length_cgu_list = len(self.creep_gen_units[player_id])
            if length_cgu_list == 0:
                break
            cgu_per_player = self.creep_gen_units[player_id][length_cgu_list - 1]
            creep_generating_died = filter(lambda x: x[0] == unit_id, cgu_per_player)
            for creep_generating_died_unit in creep_generating_died:
                new_cgu_per_player = list(
                    filter(lambda x: x != creep_generating_died_unit, cgu_per_player)
                )
                self.creep_gen_units[player_id].append(new_cgu_per_player)
                self.creep_gen_units_times[player_id].append(time_frame)

    def cgu_gen_times_to_chunks(self, cgu_time_list):
        ## this function returns the index and value of every cgu time
        maximum_cgu_time = max(cgu_time_list)
        for i in range(0, maximum_cgu_time):
            a = list(filter(lambda x_y: x_y[1] // 60 == i, enumerate(cgu_time_list)))
            if len(a) > 0:
                yield a

    def cgu_in_min_to_cgu_units(self, player_id, cgu_in_minutes):
        ## this function takes index and value of CGU times and returns
        ## the cgu units with the maximum length
        for cgu_per_minute in cgu_in_minutes:
            indexes = map(lambda x: x[0], cgu_per_minute)
            cgu_units = list()
            for index in indexes:
                cgu_units.append(self.creep_gen_units[player_id][index])
            cgu_max_in_minute = max(cgu_units, key=len)
            yield cgu_max_in_minute

    def reduce_cgu_per_minute(self, player_id):
        # the creep_gen_units_lists contains every single time frame
        # where a CGU is added,
        # To reduce the calculations required, the time frame containing
        # the most cgus every minute will be used to represent that minute
        cgu_per_minute1, cgu_per_minute2 = tee(
            self.cgu_gen_times_to_chunks(self.creep_gen_units_times[player_id])
        )
        cgu_unit_max_per_minute = self.cgu_in_min_to_cgu_units(
            player_id, cgu_per_minute1
        )
        minutes = map(lambda x: int(x[0][1] // 60) * 60, cgu_per_minute2)
        self.creep_gen_units[player_id] = list(cgu_unit_max_per_minute)
        self.creep_gen_units_times[player_id] = list(minutes)

    def get_creep_spread_area(self, player_id):
        ## iterates through all cgus and and calculate the area
        for index, cgu_per_player in enumerate(self.creep_gen_units[player_id]):
            # convert cgu list into centre of circles and radius
            cgu_radius = map(
                lambda x: (x[1], self.unit_name_to_radius[x[2]]), cgu_per_player
            )
            # convert event coords to minimap coords
            cgu_radius = self.convert_cgu_radius_event_to_map_coord(cgu_radius)
            creep_area_positions = self.cgu_radius_to_map_positions(
                cgu_radius, self.radius_to_coordinates
            )
            cgu_event_time = self.creep_gen_units_times[player_id][index]
            cgu_event_time_str = (
                str(int(cgu_event_time // 60)) + ":" + str(cgu_event_time % 60)
            )
            if self.debug:
                self.print_image(creep_area_positions, player_id, cgu_event_time_str)
            creep_area = len(creep_area_positions)
            self.creep_spread_by_minute[player_id][cgu_event_time] = (
                float(creep_area) / self.mapSize * 100
            )

        return self.creep_spread_by_minute[player_id]

    def cgu_radius_to_map_positions(self, cgu_radius, radius_to_coordinates):
        ## This function uses the output of radius_to_map_positions
        total_points_on_map = Set()
        if len(cgu_radius) == 0:
            return []
        for cgu in cgu_radius:
            point = cgu[0]
            radius = cgu[1]
            ## subtract all radius_to_coordinates with centre of
            ## cgu radius to change centre of circle
            cgu_map_position = map(
                lambda x: (x[0] + point[0], x[1] + point[1]),
                self.radius_to_coordinates[radius],
            )
            total_points_on_map = total_points_on_map | Set(cgu_map_position)
        return total_points_on_map

    def print_image(self, total_points_on_map, player_id, time_stamp):
        minimap_copy = self.minimap_image.copy()
        # Convert all creeped points to white
        for points in total_points_on_map:
            x = points[0]
            y = points[1]
            x, y = self.check_image_pixel_within_boundary(x, y)
            minimap_copy.putpixel((x, y), (255, 255, 255))
        creeped_image = minimap_copy
        # write creeped minimap image to a string as a png
        creeped_imageIO = StringIO()
        creeped_image.save(creeped_imageIO, "png")
        self.creep_spread_image_by_minute[player_id][time_stamp] = creeped_imageIO
        ##debug for print out the images
        f = open(str(player_id) + "image" + time_stamp + ".png", "w")
        f.write(creeped_imageIO.getvalue())
        creeped_imageIO.close()
        f.close()

    def check_image_pixel_within_boundary(self, pointX, pointY):
        pointX = 0 if pointX < 0 else pointX
        pointY = 0 if pointY < 0 else pointY
        # put a minus 1 to make sure the pixel is not directly on the edge
        pointX = int(self.map_width - 1 if pointX >= self.map_width else pointX)
        pointY = int(self.map_height - 1 if pointY >= self.map_height else pointY)
        return pointX, pointY

    def convert_cgu_radius_event_to_map_coord(self, cgu_radius):
        cgu_radius_new = list()
        for cgu in cgu_radius:
            x = cgu[0][0]
            y = cgu[0][1]
            (x, y) = self.convert_event_coord_to_map_coord(x, y)
            cgu = ((x, y), cgu[1])
            cgu_radius_new.append(cgu)
        return cgu_radius_new

    def convert_event_coord_to_map_coord(self, x, y):
        imageX = int(self.map_width - self.transX + self.image_scale * x)
        imageY = int(self.transY - self.image_scale * y)
        return imageX, imageY
