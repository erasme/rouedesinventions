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
from math import cos, sin, pi, degrees


class Invention(FloatLayout):

    roue = ObjectProperty()
    radius = NumericProperty(1)

    def on_touch_down(self, touch):
        super(Invention, self).on_touch_down(touch)
        if touch.is_double_tap:
            self.hide()
        return True

    def show(self):
        r = max(self.width, self.height) * 1.4
        anim = Animation(radius=r, d=r / 1500., t='out_quad')
        anim.bind(on_complete=self._show_items)
        anim.start(self)

    def _show_items(self, *args):
        pass

    def hide(self):
        anim = Animation(radius=1, d=self.radius / 2000., t='in_quad')
        anim.bind(on_complete=self._hide_self)
        anim.start(self)

    def _hide_self(self, *args):
        self.roue.hide_outer_circle()
        self.parent.remove_widget(self)


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
    item_radius = NumericProperty()
    circle_color = ListProperty([1, 1, 1, 1])
    circle_outer_hidden = BooleanProperty(True)
    circle_outer_radius = NumericProperty(10)
    children_ordered = ListProperty([])
    timer = NumericProperty()
    found = BooleanProperty(False)
    angle = NumericProperty()

    def __init__(self, **kwargs):
        super(Roue, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1 / 60.)

    def load_inventions(self, inventions):
        for item in inventions.get('items', []):
            self.create_item(**item)

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
        #self.timer += dt
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
        color_hot = [0.9411, 0.2274, 0.3137, 1]
        color_cold = [.28, .75, .92, 1]

        answers_needed = 3
        diff = [(1 - x) / answers_needed for x in color_hot]

        count = len(items)
        d = 3 * dt
        dest_color = [1 - diff[x] * count for x in range(4)]
        self.circle_color = [self.circle_color[x] - (self.circle_color[x] - dest_color[x]) * d for x in range(4)]

        if count == answers_needed:
            if self.circle_outer_hidden:
                self.show_outer_circle()
                self.circle_outer_hidden = False
        else:
            if not self.circle_outer_hidden:
                self.hide_outer_circle()
                self.circle_outer_hidden = True

    def show_outer_circle(self):
        self._invention = Invention(roue=self, size=self.size)
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
    def build(self):
        with open('data/inventions.json') as fd:
            inventions = json.load(fd)
        roue = Roue()
        roue.load_inventions(inventions)
        return roue

RoueInventionsApp().run()
