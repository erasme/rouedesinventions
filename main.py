'''
Roue des Inventions
-------------------

WIP
'''

__version__ = '0.2'

import json
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.properties import NumericProperty, ListProperty, StringProperty, \
        BooleanProperty, ObjectProperty
from kivy.vector import Vector
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.uix.image import Image
from math import cos, sin, pi, degrees
from os.path import join, dirname
from glob import glob
from functools import partial
from random import random


class InventionItem(Scatter):
    source = StringProperty()

class Invention(FloatLayout):

    roue = ObjectProperty()
    radius = NumericProperty(1)
    invention_title = StringProperty()
    invention_id = StringProperty()

    def on_touch_down(self, touch):
        super(Invention, self).on_touch_down(touch)
        if touch.is_double_tap:
            self.hide()
        return True

    def show(self):
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

    def hide(self):
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

        item = InventionItem(image=image, size=image.texture_size)
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

    item_id = StringProperty()
    item_title = StringProperty()
    item_date = StringProperty()
    item_description = StringProperty()
    item_size = NumericProperty()
    is_manual = BooleanProperty(False)
    is_cooking = BooleanProperty(False)
    item_radius = NumericProperty(100)
    first_position = BooleanProperty()
    description_sh = NumericProperty(0)
    roue = ObjectProperty()
    font_size = NumericProperty(10)
    item_scale_open = NumericProperty(1.8)
    desc_opacity = NumericProperty(0)

    _set_rotation = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_manual = True
            self.show_description()
        return super(RoueItem, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            if len(self._touches) == 1:
                self.is_manual = False
                self.hide_description()
                self.is_cooking = self.roue.collide_widget(self)
        return super(RoueItem, self).on_touch_up(touch)

    def _on_center(self, *args):
        # refresh rotation
        if not self.roue:
            return
        if self._set_rotation:
            return
        roue_center = Vector(self.roue.center)
        center = Vector(self.center)
        angle = - Vector(0, 1).angle(center - roue_center)

        self._set_rotation = True
        self.rotation = angle
        self._set_rotation = False

    def show_description(self):
        Animation(item_size=self.item_radius * self.item_scale_open,
                desc_opacity=1., d=.5, t='out_quart').start(self)

    def hide_description(self):
        Animation(item_size=self.item_radius, 
                desc_opacity=0., d=.5, t='out_quart').start(self)


class Roue(FloatLayout):

    circle_radius = NumericProperty()
    item_radius = NumericProperty(100)
    circle_color = ListProperty([1, 1, 1, 1])
    circle_outer_hidden = BooleanProperty(True)
    circle_outer_radius = NumericProperty(10)
    children_ordered = ListProperty([])
    items_count = NumericProperty(0)
    timer = NumericProperty()
    found = BooleanProperty(False)
    angle = NumericProperty()

    def __init__(self, **kwargs):
        self.bind(size=self._update_item_radius,
                items_count=self._update_item_radius)
        super(Roue, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1 / 60.)

    def _update_item_radius(self, *args):
        if self.items_count == 0:
            return
        m = min(map(float, self.size))
        p = m * pi
        r = p / self.items_count

        p -= r * 4
        r = p / self.items_count
        self.item_radius = r * 2 - pi
        self.circle_radius = m - r * 3


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
        self.timer += dt
        if not self.children:
            return
        self.update_layout(dt)
        self.check_inventions(dt)

    def update_layout(self, dt):
        count = len(self.children)
        angle_step = (pi * 2) / float(count)
        distance = min(self.width, self.height) * 0.40
        angle_timer = self.timer / 10.
        self.angle = -degrees(angle_timer)
        for index, item in enumerate(self.children_ordered):
            if not isinstance(item, RoueItem):
                continue
            if item.is_manual or item.is_cooking:
                continue

            item.item_radius = self.item_radius / 2.
            angle = angle_timer + index * angle_step
            cx = self.center_x + cos(angle) * distance
            cy = self.center_y + sin(angle) * distance
            r = degrees(angle) - 90

            if item.first_position:
                item.center = cx, cy
                item.first_position = False
                item.rotation = r
            else:
                ix, iy = item.center
                ir = item.rotation
                d = 10 * dt
                item.center_x += (cx - ix) * d
                item.center_y += (cy - iy) * d
                dr = r - ir

                if dr < -180:
                    dr += 360
                elif dr > 180:
                    dr -= 360
                item.rotation += dr * d

    def collide_widget(self, other):
        # distance calculation.
        return Vector(self.center).distance(Vector(other.center)) < self.circle_radius / 2.


    def check_inventions(self, dt):
        items = [item for item in self.children if item.is_cooking]

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

        #print (hot, cold), (hot_percent, cold_percent), value, count_inventions
        color_hot = [1 - x for x in [0.9411, 0.2274, 0.3137, 1]]
        color_cold = [1 - x for x in [.28, .75, .92, 1]]

        if value > 0: 
            dest_color = [1 - x * value for x in color_hot]
        else:
            value = -value
            dest_color = [1 - x * value for x in color_cold]

        d = 3 * dt
        self.circle_color = [self.circle_color[x] - (self.circle_color[x] - dest_color[x]) * d for x in range(4)]

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
        anim = Animation(
                circle_outer_radius=(self.circle_radius + self.item_radius),
                t='out_elastic')
        #anim += Animation()
        anim.bind(on_complete=self._show_invention)
        anim.start(self)

    def hide_outer_circle(self):
        anim = Animation(circle_outer_radius=self.circle_radius,
                t='in_elastic')
        anim.bind(on_complete=self._reset)
        anim.start(self)

    def _show_invention(self, *args):
        self._invention.show()

    def _reset(self, *args):
        self.found = False
        for child in self.children:
            if isinstance(child, RoueItem):
                child.is_manual = False
                child.is_cooking = False

class RoueInventionsApp(App):
    icon = 'data/icon.png'
    def build(self):
        with open('data/inventions.json') as fd:
            inventions = json.load(fd)
        roue = Roue()
        roue.load_inventions(inventions)
        return roue

RoueInventionsApp().run()
