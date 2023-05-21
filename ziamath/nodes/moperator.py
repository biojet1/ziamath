''' <mo> Math Operator Element '''
import xml.etree.ElementTree as ET

from ziafont.fonttypes import BBox

from ..styles import styledstr
from ..drawable import Glyph
from .. import operators
from . import Mnode
from .nodetools import elementtext, subglyph


class Moperator(Mnode, tag='mo'):
    ''' Operator math element '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        self.string = styledstr(elementtext(self.element), self.style.mathvariant)
        self.form = element.get('form', 'infix')

        # Load parameters from operators table for deciding how much space
        # to add on either side of the operator
        self.params = operators.get_params(self.string, self.form)
        self.params.update(element.attrib)
        self.width = kwargs.get('width', None)
        self.height = kwargs.get('height', None)

        minsize = self.size_px(element.get('minsize', '0'))
        maxsize = self.size_px(element.get('maxsize', '0'))
        mathsize = self.size_px(self.style.mathsize)
        if self.height:
            if minsize:
                self.height = max(self.height, minsize)
            if maxsize:
                self.height = min(self.height, maxsize)
        else:
            if mathsize:
                self.height = mathsize
            elif minsize:
                self.height = minsize
            elif maxsize:
                self.height = maxsize

        if self.string in ['|', '‖', '∣', '❘'] and self.params.get('fence') == 'true':
            # Hack around weird spacing with \middle operators
            self.params['rspace'] = 'thinmathspace'

        self._setup(**kwargs)

    def _setup(self, **kwargs):
        glyphs = [self.font.glyph(char) for char in self.string]

        if kwargs.get('sup') or kwargs.get('sub'):
            addspace = False  # Dont add lspace/rspace when in super/subscripts
            glyphs = [subglyph(g, self.font) for g in glyphs]
        else:
            addspace = True

        x = xmax = 0
        self.nodes = []

        # Add lspace
        if addspace:
            x += self.size_px(self.params.get('lspace', '0'))

        ymin = 999
        ymax = -999
        for glyph, char in zip(glyphs, self.string):
            if self.params.get('largeop') == 'true' and self.style.displaystyle:
                minh = self.font.math.consts.displayOperatorMinHeight
                glyph = self.font.math.variant(glyph.index, minh, vert=True)

            if self.width:
                glyph = self.font.math.variant(
                    glyph.index, self.points_to_units(self.width), vert=False)
            elif (self.height
                    and self.params.get('stretchy') != 'false'):
                glyph = self.font.math.variant(
                    glyph.index, self.points_to_units(self.height), vert=True)

            self.nodes.append(Glyph(
                glyph, char, self.glyphsize, self.style, **kwargs))
            self.nodexy.append((x, 0))
            xmax = max(xmax, x + self.units_to_points(glyph.path.bbox.xmax))
            x += self.units_to_points(glyph.advance())
            ymin = min(ymin, self.units_to_points(glyph.path.bbox.ymin))
            ymax = max(ymax, self.units_to_points(glyph.path.bbox.ymax))

        if addspace:
            x += self.size_px(self.params.get('rspace', '0'))
            xmax = max(xmax, x)

        try:
            xmin = self.units_to_points(glyphs[0].path.bbox.xmin)
        except IndexError:
            xmin = 0
        
        self.bbox = BBox(xmin, xmax, ymin, ymax)
