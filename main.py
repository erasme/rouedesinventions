'''
Roue des Inventions
-------------------

TODO

- fix 100 - 200 size to ratio of the window size
- clean the code
'''

__version__ = '0.5'

# specific "bad" fix for biin table at erasme.
# XXX this should not be here, but in a startscript or PYTHONPATH env instead.
import sys
sys.path.insert(0, '/home/biin/rouedesinventions/kivy')


from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.properties import NumericProperty, ListProperty, StringProperty, \
        BooleanProperty, ObjectProperty
from kivy.vector import Vector
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.uix.image import Image
from math import cos, sin, pi, degrees, radians, atan2
from os.path import join, dirname, exists
from glob import glob
from functools import partial
from random import random


def angle_short(a, b, rad=False):
    '''Return the shortest angle between 2 number
    '''
    if not rad:
        a = radians(a)
        b = radians(b)
    result = atan2(sin(b - a), cos(b - a))
    if result > 0:
        result = pi - result
    else:
        result = -pi - result
    return degrees(result)


class InventionItem(Scatter):
    '''Represent an invention itself that we can manipulate.
    '''
    pass


class Invention(FloatLayout):
    '''Represent an invention, with multiple element on it (images, text, etc.)
    '''

    roue = ObjectProperty()
    '''Ownership of the invention.
    '''

    radius = NumericProperty(1)
    '''Radius of the background circle used when entering / leaving the
    invention browsing part.
    '''

    invention_title = StringProperty()
    invention_id = StringProperty()

    def on_touch_down(self, touch):
        super(Invention, self).on_touch_down(touch)
        if touch.is_double_tap:
            self.hide()
        return True

    def show(self):
        self._do_hide = False
        Clock.schedule_once(self.hide, 30)
        for child in self.children[:]:
            if isinstance(child, InventionItem):
                self.remove_widget(child)
        r = max(self.width, self.height) * 1.4
        anim = Animation(radius=r, d=r / 1500., t='out_quad')
        anim.bind(on_complete=self._show_items)
        anim.start(self)

    def _show_items(self, *args):
        files = glob(join(dirname(__file__), 'data', 'inventions',
            self.invention_id, '*.jpg'))
        d = 0
        for fn in files:
            Clock.schedule_once(partial(
                self._show_item, fn), d)
            d += .1

    def hide(self, *dt):
        if self._do_hide:
            return
        self._do_hide = True
        anim = Animation(radius=1, d=self.radius / 2000., t='in_quad')
        anim.bind(on_complete=self._hide_self)
        anim.start(self)

    def _hide_self(self, *args):
        animc = Animation(opacity=0)
        for child in self.children:
            if isinstance(child, InventionItem):
                animc.start(child)
        self.roue.hide_outer_circle()
        self.parent.remove_widget(self)

    def _show_item(self, fn, *args):
        image = Image(source=fn)
        image.size = image.texture_size
        d_scale = 1. / (max(image.size) / (min(self.size) / 4.))

        item = InventionItem(size=image.texture_size)
        item.add_widget(image)
        item.scale = .01
        item.opacity = 0.
        item.rotation = random() * 360
        item.center = self.center

        hw, hh = [x / 2. for x in self.center]
        d_rotation = item.rotation + (random() * 20 - 10)
        d = random() * 360
        d_x = self.center_x + cos(d) * (hw / 2. + random() * hw)
        d_y = self.center_y + sin(d) * (hh / 2. + random() * hh)

        anim = Animation(opacity=1., rotation=d_rotation,
                scale=d_scale,
                center=(d_x, d_y), t='out_quad')
        anim.start(item)

        self.add_widget(item)


class RoueItem(Scatter):
    '''Item on the big wheel that user can manipulate and move within the center
    of the wheel, or outside the wheel to read the description.
    '''

    # informations from the json
    item_id = StringProperty()
    item_title = StringProperty()
    item_date = StringProperty()
    item_description = StringProperty()
    item_size = NumericProperty()
    item_filename = StringProperty()

    is_manual = BooleanProperty(False)
    '''Indicate if the item is currently manipulated by the user (True) or not
    (False)
    '''

    is_cooking = BooleanProperty(False)
    '''Indicate if the item is currently in the center of the wheel
    '''

    item_radius = NumericProperty(100)
    '''Current radius of the item
    '''

    roue = ObjectProperty()
    '''Ownership of the item
    '''

    font_size = NumericProperty(10)
    '''Font size used for text within the item
    '''

    item_scale_open = NumericProperty(1.8)
    '''Factor on how much the item should be resized during its opening. When
    closing, the factor is back to 1.
    '''

    desc_opacity = NumericProperty(0)
    '''Current opacity of the content, used for animating open/close.
    '''

    item_prev_angle = NumericProperty(0)
    '''Previous value of item_angle, used for deciding where the item should be
    inserted again when the user left the item alone.
    '''

    item_angle = NumericProperty(0)
    '''Current angle of the item related to the wheel.
    '''

    wanted_rotation = NumericProperty(0)
    '''Indicate the ideal rotation in the wheel. This is different from the
    current rotation, and is used to animate slowly the current rotation to the
    wanted rotation.
    '''

    # internals
    _set_pos = BooleanProperty(False)
    touch = ObjectProperty(None, allownone=True)

    def on_item_id(self, *args):
        # load image or animation of the item.
        zipfn = 'data/sd/{}.zip'.format(self.item_id)
        pngfn = 'data/sd/{}.png'.format(self.item_id)
        if exists(zipfn):
            self.item_filename = zipfn
        else:
            self.item_filename = pngfn

    def on_touch_down(self, touch):
        # check if the item is currently manipulated by the user or not
        if self.collide_point(*touch.pos):
            self.touch = touch
            self.is_manual = True
        return super(RoueItem, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        # don't forget to check when the user stop manipulating the item.
        if touch.grab_current == self:
            if len(self._touches) == 1:
                self.is_manual = False
                self.is_cooking = self.roue.collide_widget(self)
                self.touch = None
                self.roue.prepare_back(self)
        return super(RoueItem, self).on_touch_up(touch)

    def on_center(self, *args):
        # every time the item is moving, do some checks.
        if not self.roue:
            return
        if self._set_pos:
            return
        self._set_pos = True
        center = self.center
        pos = self.touch.pos if self.touch else self.center
        d = Vector(pos).distance(Vector(self.roue.center))
        m = 100
        if d > self.roue.circle_radius_item / 2 + m:
            self.item_size = self.item_radius * self.item_scale_open
            self.desc_opacity = 1.
        elif d < self.roue.circle_radius_item / 2:
            self.item_size = self.item_radius
            self.desc_opacity = 0.
        else:
            delta = (d - self.roue.circle_radius_item / 2) / m
            self.item_size = self.item_radius * (1 + (delta * (self.item_scale_open - 1)))
            self.desc_opacity = delta

        self.center = center
        self._set_pos = False

    @property
    def is_near_wheel(self):
        # return True is the item is near the wheel (used for deciding if the
        # item should be inserted back in the wheel or not)
        return self.distance_to_wheel < self.roue.circle_radius_item / 2. + 200.

    @property
    def angle_to_wheel(self):
        # relative angle of the item to the wheel
        v = (Vector(self.center) - Vector(self.roue.center))
        return radians(v.angle(Vector(1, 0))) % (pi * 2)

    @property
    def distance_to_wheel(self):
        # relative distance between the item and the wheel
        return Vector(self.center).distance(Vector(self.roue.center))

    @property
    def is_outside_center(self):
        # return True if the item is not currently in the center of the wheel
        # (used for deciding if it should be used for cooking or not)
        return self.distance_to_wheel > self.roue.circle_radius_item / 2. - 200


class Roue(FloatLayout):
    '''Representation of the wheel, containing all the item.
    '''

    circle_radius = NumericProperty()
    circle_radius_item = NumericProperty()
    item_radius = NumericProperty(100)
    circle_color = ListProperty([1, 1, 1, 1])
    circle_outer_hidden = BooleanProperty(True)
    children_ordered = ListProperty([])
    children_outside = ListProperty([])
    items_count = NumericProperty(0)
    timer = NumericProperty()
    found = BooleanProperty(False)
    angle = NumericProperty()
    glow_value = NumericProperty()

    def __init__(self, **kwargs):
        self.bind(size=self._update_item_radius,
                items_count=self._update_item_radius)
        super(Roue, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1 / 60.)
        self.force_position = 0

    def _update_item_radius(self, *args):
        if self.items_count == 0:
            return
        m = min(map(float, self.size))
        p = m * pi
        r = p / self.items_count
        p -= r * 4
        r = p / self.items_count
        self.item_radius = r * 2 - pi
        self.circle_radius = m - (pi * r - r) - 50
        self.circle_radius_item = self.circle_radius + self.item_radius


    def load_inventions(self, data):
        items = data.get('items', [])
        self.items_count = len(items)
        for item in items:
            self.create_item(**item)

        ids = [x.get('id') for x in items]

        inventions = data.get('inventions', [])

        self.inventions = {}
        self.items_to_inventions = {}

        for invention in inventions:
            self.inventions[invention.get('id')] = invention
            for item in invention.get('items', []):
                if item not in self.items_to_inventions:
                    self.items_to_inventions[item] = []
                self.items_to_inventions[item].append(invention.get('id'))
                if item not in ids:
                    print 'WARNING: Invention {} missing {}'.format(
                        invention.get('id'), item)

    def create_item(self, id, title, description, date):
        item = RoueItem(item_id=id, item_title=title,
                item_date=date, item_description=description,
                item_radius=self.item_radius / 2.,
                roue=self)
        self.children_ordered.append(item)
        self.add_widget(item)

    def update(self, dt):
        if self.found:
            return
        self.timer += dt * .25
        if not self.children_ordered:
            return
        self.update_layout(dt)
        self.check_inventions(dt)
        self.glow_value = cos(self.timer * 3.)

    def prepare_back(self, item):
        if item not in self.children_ordered:
            return
        self.children_ordered.remove(item)
        self.children_outside.append(item)

    def insert_back(self, item):
        # insert an item within the wheel, at the right place.
        if item in self.children_ordered:
            self.children_ordered.remove(item)
        else:
            self.children_outside.remove(item)
        v = (Vector(item.center) - Vector(self.center))
        angle = radians(v.angle(Vector(1, 0))) % (pi * 2)

        # reorder our list to simplify our insertion
        self.children_ordered = sorted(self.children_ordered,
                key=lambda x: x.item_angle % (pi * 2))

        for index, child in enumerate(self.children_ordered):
            if child.item_angle % (pi * 2) > angle:
                break

        if index == len(self.children_ordered) - 1:
            # select the shortest angle
            a = angle_short(self.children_ordered[0].item_angle, angle, rad=True)
            b = angle_short(self.children_ordered[-1].item_angle, angle, rad=True)
            if a < b:
                index = 0
        self.children_ordered.insert(index, item)
        item.item_angle = item.item_prev_angle = angle

    def update_layout(self, dt):
        count = len(self.children_ordered)
        angle_step = (pi * 2) / float(count)
        distance = min(self.width, self.height) * 0.40
        angle_timer = self.timer / 10.
        self.angle = -degrees(angle_timer)
        d = min(1, dt)

        # during few iteration, we need to force size / position and
        # rotation. This is for handling window resizing.
        if self.force_position < 2:
            for index, item in enumerate(self.children_ordered):
                item.item_radius = self.item_radius / 2.

                angle = angle_timer + index * angle_step
                cx = self.center_x + cos(angle) * distance
                cy = self.center_y + sin(angle) * distance
                r = degrees(angle) - 90

                item.center = cx, cy
                item.item_angle = item.item_prev_angle = angle
                item.wanted_rotation = r
                item.rotation = item.wanted_rotation + 180

            self.force_position += 1
            return


        # nicer insertion if the item is manipulated by the user
        for item in self.children_outside + self.children_ordered:
            if not item.is_manual:
                continue
            if item.is_near_wheel:
                self.insert_back(item)
            else:
                self.prepare_back(item)

        # all the widgets going on outside the wheel is moving back slowly to
        # the wheel
        for item in self.children_outside[:]:
            if item.is_manual:
                continue

            if item.is_near_wheel:
                self.insert_back(item)
                continue

            item_distance = item.distance_to_wheel
            diff_distance = item_distance - distance

            if diff_distance > 1.:
                diff_distance *= dt
                dmax = 50 * dt
                if diff_distance > dmax:
                    diff_distance = dmax
                elif diff_distance < -dmax:
                    diff_distance = -dmax
                item_distance -= diff_distance

            cx = self.center_x + cos(item.angle_to_wheel) * item_distance
            cy = self.center_y + sin(item.angle_to_wheel) * item_distance
            item.center = cx, cy


        # that's the most important part: position the item equally between
        # previous and next children
        children = self.children_ordered[:]
        for index, item in enumerate(children):

            item.item_radius = self.item_radius / 2.

            item_prev = children[(index - 1) % len(children)]
            item_next = children[(index + 1) % len(children)]

            # get our position on the wheel
            current_angle = item.item_angle
            prev_angle = item_prev.item_prev_angle
            next_angle = item_next.item_prev_angle

            # try to be between both angle
            if prev_angle > next_angle:
                prev_angle -= pi * 2
            dest_angle = (next_angle + prev_angle) / 2.

            if dest_angle > current_angle:
                dest_angle -= pi * 2
            distance_angle = current_angle - dest_angle

            if distance_angle > pi:
                distance_angle -= pi * 2
            elif distance_angle < -pi:
                distance_angle += pi * 2

            item.item_angle -= distance_angle * d * 4

        # then, move them slowly to the position we wanted
        children = [x for x in self.children_ordered if not x.is_manual]
        for index, item in enumerate(children):
            item.item_angle += d * 0.03
            item.item_angle %= pi * 2

            item_distance = item.distance_to_wheel
            diff_distance = item_distance - distance
            if abs(diff_distance) > 1:
                diff_distance *= dt
                if not item.is_outside_center:
                    diff_distance /= 10.
                item_distance -= diff_distance

            cx = self.center_x + cos(item.item_angle) * item_distance
            cy = self.center_y + sin(item.item_angle) * item_distance
            item.center = cx, cy

            # adjust the rotation
            if item.is_near_wheel:
                rotation = (degrees(item.angle_to_wheel) + 90)
                item.wanted_rotation += angle_short(rotation, item.wanted_rotation) * d
                item.rotation = item.wanted_rotation + 180

            if item.is_outside_center:
                item.is_cooking = False


        for index, item in enumerate(children):
            item.item_prev_angle = item.item_angle


    def on_size(self, *args):
        self.force_position = 0

    def collide_widget(self, other):
        # distance calculation.
        return Vector(self.center).distance(Vector(other.center)) < self.circle_radius / 2.

    def check_inventions(self, dt):
        items = [item for item in self.children_ordered if item.is_cooking]

        # search if some item inventions match
        count_inventions = {}
        cold = hot = 0
        for item in items:
            if item.item_id not in self.items_to_inventions:
                cold += 1
                continue
            for invention_id in self.items_to_inventions.get(item.item_id, []):
                if invention_id not in count_inventions:
                    count_inventions[invention_id] = 1
                else:
                    count_inventions[invention_id] += 1

        if count_inventions:
            hot += max(count_inventions.values())

        hot_percent = 0
        hot_item_needed = 0
        hot_invention = None
        for invention_id, count in count_inventions.items():
            invention = self.inventions[invention_id]
            item_needed = len(invention.get('items'))
            percent = count / float(item_needed)
            hot_percent = max(percent, hot_percent)
            if hot_percent == percent:
                hot_item_needed = item_needed
                hot_invention = invention_id

        if hot_item_needed != len(items) and hot_percent:
            hot_percent -= 0.1

        cold_percent = cold / 3.
        value = hot_percent - cold_percent

        if len(count_inventions) > 1 and len(items) != 1:
            value = -1
        else:
            value = hot_percent

        color_hot = [1 - x for x in [0.90, 0.0, 0.0]]
        color_cold = [1 - x for x in [.28, .75, .92]]

        if value > 0:
            dest_color = [.91 - x * value for x in color_hot]
        elif value == 0:
            dest_color = [.91] * 3
        else:
            value = 1
            dest_color = [.91 - x * value for x in color_cold]

        d = dt
        self.circle_color = [self.circle_color[x] - (self.circle_color[x] - dest_color[x]) * d for x in range(3)]
        if hot_percent == 1:
            if self.circle_outer_hidden:
                self.show_outer_circle(hot_invention)
                self.circle_outer_hidden = False
        else:
            if not self.circle_outer_hidden:
                self.hide_outer_circle()
                self.circle_outer_hidden = True

    def show_outer_circle(self, invention_id):
        invention = self.inventions[invention_id]
        self._invention = Invention(roue=self, size=self.size,
                invention_title=invention.get('title'),
                invention_id=invention.get('id'))
        self.add_widget(self._invention)
        self.found = True
        self._invention.show()

    def hide_outer_circle(self):
        self.found = False
        for child in self.children:
            if isinstance(child, RoueItem):
                child.is_manual = False
                child.is_cooking = False


if __name__ == '__main__':

    from kivy.app import App
    import json
    import os

    class RoueInventionsApp(App):

        icon = 'data/icon.png'

        def build(self):
            directory = os.path.dirname(__file__)
            with open(directory+'/data/inventions.json') as fd:
                inventions = json.load(fd)
            roue = Roue()
            roue.load_inventions(inventions)
            return roue

    RoueInventionsApp().run()

