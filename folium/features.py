# -*- coding: utf-8 -*-
"""
Features
------

Extra features Elements.
"""
from jinja2 import Template
import json

from .utilities import (_parse_size,
                        _locations_mirror, _locations_tolist, image_to_url,
                        text_type, binary_type,
                        none_min, none_max, iter_points,
                        )

from .element import Element, Figure, JavascriptLink, CssLink, MacroElement
from .map import Layer, Icon, Marker, Popup


class WmsTileLayer(Layer):
    """Creates a Web Map Service (WMS) layer.

    Parameters
    ----------
    url : str
        The url of the WMS server.
    name : string, default None
        The name of the Layer, as it will appear in LayerControls
    layers : str, default None
        The names of the layers to be displayed.
    styles : str, default None
        Comma-separated list of WMS styles.
    format : str, default None
        The format of the service output.
        Ex: 'iamge/png'
    transparent: bool, default True
        Whether the layer shall allow transparency.
    version : str, default '1.1.1'
        Version of the WMS service to use.
    attr : str, default None
        The attribution of the service.
        Will be displayed in the bottom right corner.
    overlay : bool, default False
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls

    For more information see:
    http://leafletjs.com/reference.html#tilelayer-wms

    """
    def __init__(self, url, name=None, layers=None, styles=None, format=None,
                 transparent=True, version='1.1.1', attr=None, overlay=True,
                 control=True):
        super(WmsTileLayer, self).__init__(overlay=overlay, control=control, name=name)  # noqa
        self.url = url
        self.attribution = attr if attr is not None else ''
        # Options.
        self.layers = layers if layers else ''
        self.styles = styles if styles else ''
        self.format = format if format else 'image/jpeg'
        self.transparent = transparent
        self.version = version
        # FIXME: Should be map CRS!
        # self.crs = crs if crs else 'null
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            var {{this.get_name()}} = L.tileLayer.wms(
                '{{ this.url }}',
                {
                    layers: '{{ this.layers }}',
                    styles: '{{ this.styles }}',
                    format: '{{ this.format }}',
                    transparent: {{ this.transparent.__str__().lower() }},
                    version: '{{ this.version }}',
                    {% if this.attribution %} attribution: '{{this.attribution}}'{% endif %}
                    }
                ).addTo({{this._parent.get_name()}});

        {% endmacro %}
        """)  # noqa


class RegularPolygonMarker(Marker):
    """Custom markers using the Leaflet Data Vis Framework.

    Parameters
    ----------
    location: tuple or list, default None
        Latitude and Longitude of Marker (Northing, Easting)
    color: string, default 'black'
        Marker line color
    opacity: float, default 1
        Line opacity, scale 0-1
    weight: int, default 2
        Stroke weight in pixels
    fill_color: string, default 'blue'
        Marker fill color
    fill_opacity: float, default 1
        Marker fill opacity
    number_of_sides: int, default 4
        Number of polygon sides
    rotation: int, default 0
        Rotation angle in degrees
    radius: int, default 15
        Marker radius, in pixels
    popup: string or folium.Popup, default None
        Input text or visualization for object. Can pass either text,
        or a folium.Popup object.
        If None, no popup will be displayed.

    Returns
    -------
    Polygon marker names and HTML in obj.template_vars

    For more information, see https://humangeo.github.io/leaflet-dvf/
    """
    def __init__(self, location, color='black', opacity=1, weight=2,
                 fill_color='blue', fill_opacity=1,
                 number_of_sides=4, rotation=0, radius=15, popup=None):
        super(RegularPolygonMarker, self).__init__(location, popup=popup)
        self._name = 'RegularPolygonMarker'
        self.color = color
        self.opacity = opacity
        self.weight = weight
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity
        self.number_of_sides = number_of_sides
        self.rotation = rotation
        self.radius = radius

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
            var {{this.get_name()}} = new L.RegularPolygonMarker(
                new L.LatLng({{this.location[0]}},{{this.location[1]}}),
                {
                    icon : new L.Icon.Default(),
                    color: '{{this.color}}',
                    opacity: {{this.opacity}},
                    weight: {{this.weight}},
                    fillColor: '{{this.fill_color}}',
                    fillOpacity: {{this.fill_opacity}},
                    numberOfSides: {{this.number_of_sides}},
                    rotation: {{this.rotation}},
                    radius: {{this.radius}}
                    }
                )
                .addTo({{this._parent.get_name()}});
            {% endmacro %}
            """)

    def render(self, **kwargs):
        """Renders the HTML representation of the element."""
        super(RegularPolygonMarker, self).render()

        figure = self.get_root()
        assert isinstance(figure, Figure), ("You cannot render this Element "
                                            "if it's not in a Figure.")

        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/leaflet-dvf/0.2/leaflet-dvf.markers.min.js"),  # noqa
            name='dvf_js')


class Vega(Element):
    """Cretes a Vega chart element.

    Parameters
    ----------
    data: JSON-like str or object
        The Vega description of the chart.
        It can also be any object that has a method `to_json`,
        so that you can (for instance) provide a `vincent` chart.
    width: int or str, default None
        The width of the output element.
        If None, either data['width'] (if available) or '100%' will be used.
        Ex: 120, '120px', '80%'
    height: int or str, default None
        The height of the output element.
        If None, either data['width'] (if available) or '100%' will be used.
        Ex: 120, '120px', '80%'
    left: int or str, default '0%'
        The horizontal distance of the output with respect to the parent
        HTML object. Ex: 120, '120px', '80%'
    top: int or str, default '0%'
        The vertical distance of the output with respect to the parent
        HTML object. Ex: 120, '120px', '80%'
    position: str, default 'relative'
        The `position` argument that the CSS shall contain.
        Ex: 'relative', 'absolute'
    """
    def __init__(self, data, width=None, height=None,
                 left="0%", top="0%", position='relative'):
        super(Vega, self).__init__()
        self._name = 'Vega'
        self.data = data.to_json() if hasattr(data, 'to_json') else data
        # FIXME:
        if isinstance(self.data, text_type) or isinstance(data, binary_type):
            self.data = json.loads(self.data)

        # Size Parameters.
        self.width = _parse_size(self.data.get('width', '100%') if
                                 width is None else width)
        self.height = _parse_size(self.data.get('height', '100%') if
                                  height is None else height)
        self.left = _parse_size(left)
        self.top = _parse_size(top)
        self.position = position
        self._template = Template(u"")

    def render(self, **kwargs):
        """Renders the HTML representation of the element."""
        self.json = json.dumps(self.data)

        self._parent.html.add_children(Element(Template("""
            <div id="{{this.get_name()}}"></div>
            """).render(this=self, kwargs=kwargs)), name=self.get_name())

        self._parent.script.add_children(Element(Template("""
            vega_parse({{this.json}},{{this.get_name()}});
            """).render(this=self)), name=self.get_name())

        figure = self.get_root()
        assert isinstance(figure, Figure), ("You cannot render this Element "
                                            "if it's not in a Figure.")

        figure.header.add_children(Element(Template("""
            <style> #{{this.get_name()}} {
                position : {{this.position}};
                width : {{this.width[0]}}{{this.width[1]}};
                height: {{this.height[0]}}{{this.height[1]}};
                left: {{this.left[0]}}{{this.left[1]}};
                top: {{this.top[0]}}{{this.top[1]}};
            </style>
            """).render(this=self, **kwargs)), name=self.get_name())

        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js"),  # noqa
            name='d3')

        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/vega/1.4.3/vega.min.js"),  # noqa
            name='vega')

        figure.header.add_children(
            JavascriptLink("https://code.jquery.com/jquery-2.1.0.min.js"),
            name='jquery')

        figure.script.add_children(
            Template("""function vega_parse(spec, div) {
            vg.parse.spec(spec, function(chart) { chart({el:div}).update(); });}"""),  # noqa
            name='vega_parse')


class GeoJson(Layer):
    """Creates a GeoJson object for plotting into a Map.

    Parameters
    ----------
    data: file, dict or str.
        The GeoJSON data you want to plot.
        * If file, then data will be read in the file and fully
        embedded in Leaflet's JavaScript.
        * If dict, then data will be converted to JSON and embedded
        in the JavaScript.
        * If str, then data will be passed to the JavaScript as-is.
    style_function: function, default None
        A function mapping a GeoJson Feature to a style dict.
    name : string, default None
        The name of the Layer, as it will appear in LayerControls
    overlay : bool, default False
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls

    Examples
    --------
    >>> # Providing file that shall be embeded.
    >>> GeoJson(open('foo.json'))
    >>> # Providing filename that shall not be embeded.
    >>> GeoJson('foo.json')
    >>> # Providing dict.
    >>> GeoJson(json.load(open('foo.json')))
    >>> # Providing string.
    >>> GeoJson(open('foo.json').read())

    >>> # Provide a style_function that color all states green but Alabama.
    >>> style_function = lambda x: {'fillColor': '#0000ff' if
    ...                             x['properties']['name']=='Alabama' else
    ...                             '#00ff00'}
    >>> GeoJson(geojson, style_function=style_function)
    """
    def __init__(self, data, style_function=None, name=None,
                 overlay=True, control=True):
        super(GeoJson, self).__init__(name=name, overlay=overlay,
                                      control=control)
        self._name = 'GeoJson'
        if hasattr(data, 'read'):
            self.embed = True
            self.data = json.load(data)
        elif isinstance(data, dict):
            self.embed = True
            self.data = data
        elif isinstance(data, text_type) or isinstance(data, binary_type):
            if data.lstrip()[0] in '[{':  # This is a GeoJSON inline string
                self.embed = True
                self.data = json.loads(data)
            else:  # This is a filename
                self.embed = False
                self.data = data
        elif data.__class__.__name__ in ['GeoDataFrame', 'GeoSeries']:
            self.embed = True
            if hasattr(data, '__geo_interface__'):
                # We have a GeoPandas 0.2 object.
                self.data = json.loads(json.dumps(data.to_crs(epsg='4326').__geo_interface__))  # noqa
            elif hasattr(data, 'columns'):
                # We have a GeoDataFrame 0.1
                self.data = json.loads(data.to_crs(epsg='4326').to_json())
            else:
                msg = 'Unable to transform this object to a GeoJSON.'
                raise ValueError(msg)
        else:
            raise ValueError('Unhandled object {!r}.'.format(data))

        if style_function is None:
            def style_function(x):
                return {}
        self.style_function = style_function

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                var {{this.get_name()}} = L.geoJson(
                    {% if this.embed %}{{this.style_data()}}{% else %}"{{this.data}}"{% endif %})
                    .addTo({{this._parent.get_name()}});
                {{this.get_name()}}.setStyle(function(feature) {return feature.properties.style;});
            {% endmacro %}
            """)  # noqa

    def style_data(self):
        """
        Applies `self.style_function` to each feature of `self.data` and
        returns a corresponding JSON output.

        """
        if 'features' not in self.data.keys():
            # Catch case when GeoJSON is just a single Feature or a geometry.
            if not (isinstance(self.data, dict) and 'geometry' in self.data.keys()):  # noqa
                # Catch case when GeoJSON is just a geometry.
                self.data = {'type': 'Feature', 'geometry': self.data}
            self.data = {'type': 'FeatureCollection', 'features': [self.data]}

        for feature in self.data['features']:
            feature.setdefault('properties', {}).setdefault('style', {}).update(self.style_function(feature))  # noqa
        return json.dumps(self.data, sort_keys=True)

    def _get_self_bounds(self):
        """Computes the bounds of the object itself (not including it's children)
        in the form [[lat_min, lon_min], [lat_max, lon_max]]
        """
        if not self.embed:
            raise ValueError('Cannot compute bounds of non-embedded GeoJSON.')

        if 'features' not in self.data.keys():
            # Catch case when GeoJSON is just a single Feature or a geometry.
            if not (isinstance(self.data, dict) and 'geometry' in self.data.keys()):  # noqa
                # Catch case when GeoJSON is just a geometry.
                self.data = {'type': 'Feature', 'geometry': self.data}
            self.data = {'type': 'FeatureCollection', 'features': [self.data]}

        bounds = [[None, None], [None, None]]
        for feature in self.data['features']:
            for point in iter_points(feature.get('geometry', {}).get('coordinates', {})):  # noqa
                bounds = [
                    [
                        none_min(bounds[0][0], point[1]),
                        none_min(bounds[0][1], point[0]),
                        ],
                    [
                        none_max(bounds[1][0], point[1]),
                        none_max(bounds[1][1], point[0]),
                        ],
                    ]
        return bounds


class TopoJson(Layer):
    """Creates a TopoJson object for plotting into a Map.

    Parameters
    ----------
    data: file, dict or str.
        The TopoJSON data you want to plot.
        * If file, then data will be read in the file and fully
        embedded in Leaflet's JavaScript.
        * If dict, then data will be converted to JSON and embedded
        in the JavaScript.
        * If str, then data will be passed to the JavaScript as-is.
    object_path: str
        The path of the desired object into the TopoJson structure.
        Ex: 'objects.myobject'.
    style_function: function, default None
        A function mapping a TopoJson geometry to a style dict.
    name : string, default None
        The name of the Layer, as it will appear in LayerControls
    overlay : bool, default False
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls

    Examples
    --------
    >>> # Providing file that shall be embeded.
    >>> TopoJson(open('foo.json'), 'object.myobject')
    >>> # Providing filename that shall not be embeded.
    >>> TopoJson('foo.json', 'object.myobject')
    >>> # Providing dict.
    >>> TopoJson(json.load(open('foo.json')), 'object.myobject')
    >>> # Providing string.
    >>> TopoJson(open('foo.json').read(), 'object.myobject')

    >>> # Provide a style_function that color all states green but Alabama.
    >>> style_function = lambda x: {'fillColor': '#0000ff' if
    ...                             x['properties']['name']=='Alabama' else
    ...                             '#00ff00'}
    >>> TopoJson(topo_json, 'object.myobject', style_function=style_function)
    """
    def __init__(self, data, object_path, style_function=None,
                 name=None, overlay=True, control=True):
        super(TopoJson, self).__init__(name=name, overlay=overlay,
                                       control=control)
        self._name = 'TopoJson'
        if 'read' in dir(data):
            self.embed = True
            self.data = json.load(data)
        elif type(data) is dict:
            self.embed = True
            self.data = data
        else:
            self.embed = False
            self.data = data

        self.object_path = object_path

        if style_function is None:
            def style_function(x):
                return {}
        self.style_function = style_function

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                var {{this.get_name()}}_data = {{this.style_data()}};
                var {{this.get_name()}} = L.geoJson(topojson.feature(
                    {{this.get_name()}}_data,
                    {{this.get_name()}}_data.{{this.object_path}}
                    )).addTo({{this._parent.get_name()}});
                {{this.get_name()}}.setStyle(function(feature) {return feature.properties.style;});

            {% endmacro %}
            """)  # noqa

    def style_data(self):
        """
        Applies self.style_function to each feature of self.data and returns
        a corresponding JSON output.

        """
        def recursive_get(data, keys):
            if len(keys):
                return recursive_get(data.get(keys[0]), keys[1:])
            else:
                return data
        geometries = recursive_get(self.data, self.object_path.split('.'))['geometries']  # noqa
        for feature in geometries:
            feature.setdefault('properties', {}).setdefault('style', {}).update(self.style_function(feature))  # noqa
        return json.dumps(self.data, sort_keys=True)

    def render(self, **kwargs):
        """Renders the HTML representation of the element."""
        super(TopoJson, self).render(**kwargs)

        figure = self.get_root()
        assert isinstance(figure, Figure), ("You cannot render this Element "
                                            "if it's not in a Figure.")

        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/topojson/1.6.9/topojson.min.js"),  # noqa
            name='topojson')

    def _get_self_bounds(self):
        """Computes the bounds of the object itself (not including it's children)
        in the form [[lat_min, lon_min], [lat_max, lon_max]]
        """
        if not self.embed:
            raise ValueError('Cannot compute bounds of non-embedded TopoJSON.')

        xmin, xmax, ymin, ymax = None, None, None, None

        for arc in self.data['arcs']:
            x, y = 0, 0
            for dx, dy in arc:
                x += dx
                y += dy
                xmin = none_min(x, xmin)
                xmax = none_max(x, xmax)
                ymin = none_min(y, ymin)
                ymax = none_max(y, ymax)
        return [
            [
                self.data['transform']['translate'][1] + self.data['transform']['scale'][1] * ymin,  # noqa
                self.data['transform']['translate'][0] + self.data['transform']['scale'][0] * xmin  # noqa
            ],
            [
                self.data['transform']['translate'][1] + self.data['transform']['scale'][1] * ymax,  # noqa
                self.data['transform']['translate'][0] + self.data['transform']['scale'][0] * xmax  # noqa
            ]

        ]


class MarkerCluster(Layer):
    """Creates a MarkerCluster element to append into a map with
    Map.add_children.

    Parameters
    ----------
    name : string, default None
        The name of the Layer, as it will appear in LayerControls
    overlay : bool, default False
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls
    """
    def __init__(self, name=None, overlay=True, control=True):
        super(MarkerCluster, self).__init__(name=name, overlay=overlay,
                                            control=control)
        self._name = 'MarkerCluster'
        self._template = Template(u"""
            {% macro script(this, kwargs) %}
            var {{this.get_name()}} = L.markerClusterGroup();
            {{this._parent.get_name()}}.addLayer({{this.get_name()}});
            {% endmacro %}
            """)

    def render(self, **kwargs):
        """Renders the HTML representation of the element."""
        super(MarkerCluster, self).render()

        figure = self.get_root()
        assert isinstance(figure, Figure), ("You cannot render this Element "
                                            "if it's not in a Figure.")
        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/0.4.0/leaflet.markercluster-src.js"),  # noqa
            name='marker_cluster_src')

        figure.header.add_children(
            JavascriptLink("https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/0.4.0/leaflet.markercluster.js"),  # noqa
            name='marker_cluster')

        figure.header.add_children(
            CssLink("https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/0.4.0/MarkerCluster.css"),  # noqa
            name='marker_cluster_css')

        figure.header.add_children(
            CssLink("https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/0.4.0/MarkerCluster.Default.css"),  # noqa
            name="marker_cluster_default_css")


class DivIcon(MacroElement):
    """
    Represents a lightweight icon for markers that uses a simple `div`
    element instead of an image.

    Parameters
    ----------
    icon_size : tuple of 2 int
        Size of the icon image in pixels.
    icon_anchor : tuple of 2 int
        The coordinates of the "tip" of the icon
        (relative to its top left corner).
        The icon will be aligned so that this point is at the
        marker's geographical location.
    popup_anchor : tuple of 2 int
        The coordinates of the point from which popups will "open",
        relative to the icon anchor.
    class_name : string
        A custom class name to assign to the icon.
        Leaflet defaults is 'leaflet-div-icon' which draws a little white
        square with a shadow.  We set it 'empty' in folium.
    html : string
        A custom HTML code to put inside the div element.

    For more information see:
    http://leafletjs.com/reference.html#divicon
    """
    def __init__(self, html=None, icon_size=None, icon_anchor=None,
                 popup_anchor=None, class_name='empty'):
        super(DivIcon, self).__init__()
        self._name = 'DivIcon'
        self.icon_size = icon_size
        self.icon_anchor = icon_anchor
        self.popup_anchor = popup_anchor
        self.html = html
        self.className = class_name

        self._template = Template(u"""
            {% macro script(this, kwargs) %}

                var {{this.get_name()}} = L.divIcon({
                    {% if this.icon_size %}iconSize: [{{this.icon_size[0]}},{{this.icon_size[1]}}],{% endif %}
                    {% if this.icon_anchor %}iconAnchor: [{{this.icon_anchor[0]}},{{this.icon_anchor[1]}}],{% endif %}
                    {% if this.popup_anchor %}popupAnchor: [{{this.popup_anchor[0]}},{{this.popup_anchor[1]}}],{% endif %}
                    {% if this.className %}className: '{{this.className}}',{% endif %}
                    {% if this.html %}html: '{{this.html}}',{% endif %}
                    });
                {{this._parent.get_name()}}.setIcon({{this.get_name()}});
            {% endmacro %}
            """)  # noqa


class CircleMarker(Marker):
    """Creates a CircleMarker object for plotting on a Map.

    Parameters
    ----------
    location: tuple or list, default None
        Latitude and Longitude of Marker (Northing, Easting)
    radius: int
        The radius of the circle in pixels.
    color: str, default 'black'
        The color of the marker's edge in a HTML-compatible format.
    fill_color: str, default 'black'
        The fill color of the marker in a HTML-compatible format.
    fill_opacity: float, default à.6
        The fill opacity of the marker, between 0. and 1.
    popup: string or folium.Popup, default None
        Input text or visualization for object.
    """
    def __init__(self, location, radius=500, color='black',
                 fill_color='black', fill_opacity=0.6, popup=None):
        super(CircleMarker, self).__init__(location, popup=popup)
        self._name = 'CircleMarker'
        self.radius = radius
        self.color = color
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity

        self._template = Template(u"""
            {% macro script(this, kwargs) %}

            var {{this.get_name()}} = L.circle(
                [{{this.location[0]}},{{this.location[1]}}],
                {{ this.radius }},
                {
                    color: '{{ this.color }}',
                    fillColor: '{{ this.fill_color }}',
                    fillOpacity: {{ this.fill_opacity }}
                    }
                )
                .addTo({{this._parent.get_name()}});
            {% endmacro %}
            """)


class LatLngPopup(MacroElement):
    """
    When one clicks on a Map that contains a LatLngPopup,
    a popup is shown that displays the latitude and longitude of the pointer.

    """
    def __init__(self):
        super(LatLngPopup, self).__init__()
        self._name = 'LatLngPopup'

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                var {{this.get_name()}} = L.popup();
                function latLngPop(e) {
                    {{this.get_name()}}
                        .setLatLng(e.latlng)
                        .setContent("Latitude: " + e.latlng.lat.toFixed(4) +
                                    "<br>Longitude: " + e.latlng.lng.toFixed(4))
                        .openOn({{this._parent.get_name()}});
                    }
                {{this._parent.get_name()}}.on('click', latLngPop);
            {% endmacro %}
            """)  # noqa


class ClickForMarker(MacroElement):
    """When one clicks on a Map that contains a ClickForMarker, a Marker is created
    at the pointer's position.

    Parameters
    ----------
    popup: str, default None
        Text to display in the markers' popups.
        If None, the popups will display the marker's latitude and longitude.
    """
    def __init__(self, popup=None):
        super(ClickForMarker, self).__init__()
        self._name = 'ClickForMarker'

        if popup:
            self.popup = ''.join(['"', popup, '"'])
        else:
            self.popup = '"Latitude: " + lat + "<br>Longitude: " + lng '

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                function newMarker(e){
                    var new_mark = L.marker().setLatLng(e.latlng).addTo({{this._parent.get_name()}});
                    new_mark.dragging.enable();
                    new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
                    var lat = e.latlng.lat.toFixed(4),
                       lng = e.latlng.lng.toFixed(4);
                    new_mark.bindPopup({{ this.popup }});
                    };
                {{this._parent.get_name()}}.on('click', newMarker);
            {% endmacro %}
            """)  # noqa

class ClickForDepot(MacroElement):
    """When one clicks on a Map that contains a ClickForDepot, a Depot is created
    at the pointer's position.

    Parameters
    ----------
    popup: str, default None
        Text to display in the markers' popups.
        If None, the popups will display the marker's latitude and longitude.
    """
    def __init__(self, account_id, initial_bounds, initial_labels):
        super(ClickForDepot, self).__init__()
        self._name = 'ClickForDepot'
        self.account_id = account_id
        self.initial_bounds = initial_bounds
        self.initial_labels = initial_labels
        
        self._template = Template(u"""
            {% macro script(this, kwargs) %}


                var legend = L.control({position: 'bottomright'});
                
                legend.onAdd = function (map) {
                    var div = L.DomUtil.create('div', 'info legend');
                    div.innerHTML = '<h4>Detect depots!</h4><br>';
                    div.innerHTML += '<b>Usage:</b><br>';
                    div.innerHTML += '- &larr;&uarr;&darr;&rarr;: move box<br>';
                    div.innerHTML += '- W/A/S/D: modify box width/height<br>';
                    div.innerHTML += '- J/K: select previous/next box<br>';
                    div.innerHTML += '- click: select box<br>';
                    div.innerHTML += '- SPACE/double click: change label<br>';
                    div.innerHTML += '- DEL(CANC): remove box<br>'; 
                    div.innerHTML += '- +/-: zoom in/out<br><br>';
                    div.innerHTML += '<button onclick=saveFile() tabIndex="-1"><h5>Save to file</h5></button>';
                    
                    div.style.background = "white";
                    div.style.padding = "6px 8px";
                    return div;
                };
                {{this._parent.get_name()}}.addControl(legend);

                function getCenter(box){
                    return [(box[0][0] + box[1][0])/2,(box[0][1] + box[1][1])/2]
                }
                
               
                var discarded = [] 
                var initial_bounds = {{this.initial_bounds}};
                var initial_labels = {{this.initial_labels}};
                var depots = [];
                var depot_rectangles = [];
                var depot_markers = [];

                var selected = 0;
                var good = initial_labels.length;
 
		var home_icon = L.AwesomeMarkers.icon({
                    icon: 'home',
                    iconColor: 'white',
                    markerColor: 'green'
                    });

		var depot_icon = L.AwesomeMarkers.icon({
                    icon: 'briefcase', prefix: 'fa', 
                    iconColor: 'white',
                    markerColor: 'red'
                    });

                var unkown_icon = L.AwesomeMarkers.icon({
                    icon: 'question', prefix: 'fa', 
                    iconColor: 'white',
                    markerColor: 'blue'
                    });

		function dehighlight(i) {
                    var group = depots[i];
                    var marker = group.getLayers()[0];
                    var rectangle = group.getLayers()[1];
                    rectangle.setStyle({opacity: 0.3, fillOpacity: 0.1});
                    marker.setOpacity(0.5);
                }

                function highlight(i) {
                    var group = depots[i];
                    var marker = group.getLayers()[0];
                    var rectangle = group.getLayers()[1];
                    rectangle.setStyle({opacity: 0.7, fillOpacity: 0.5});
                    marker.setOpacity(1.0);
                    var latlng = marker.getLatLng();
                    var bounds = rectangle.getBounds();
                    bounds = [  [bounds.getNorth(), bounds.getEast()],
                                [bounds.getSouth(), bounds.getWest()]
                                ];
                    var height = bounds[1][0] - bounds[0][0];
                    var width = bounds[1][1] - bounds[0][1];
                    var center = [latlng.lat, latlng.lng];
                    bounds[0] = [center[0] - height*3, center[1] - width*4];
                    bounds[1] = [center[0] + height*3, center[1] + width*4];
                    {{this._parent.get_name()}}.fitBounds(bounds);
                    group.bringToFront();
                }

                function setLabel(i, label) { 
                    depots[i].label = label;
                    switch(label) {
                        case 'depot':
                            depot_markers[i].setIcon(depot_icon);
                            depot_rectangles[i].setStyle({color: 'red', fillColor: 'red'});
                            break;
                        case 'home':
                            depot_markers[i].setIcon(home_icon);
                            depot_rectangles[i].setStyle({color: 'green', fillColor: 'green'});
                            break;
                        default:
                            depot_markers[i].setIcon(unkown_icon);
                            depot_rectangles[i].setStyle({color: 'blue', fillColor: 'blue'});
                            break;
                    }
                }

                function rotateRole(i) {
                    console.log(depots[i].label)
                    if(depots[i].label == 'home')
                        setLabel(i, 'depot')
                    else
                        setLabel(i, 'home')
                }
                for(var i=0; i<initial_bounds.length; ++i) {
                    depot_rectangles.push(L.rectangle(initial_bounds[i]));
                    depot_markers.push(L.marker(getCenter(initial_bounds[i]),{draggable: true}));
                    depots.push(L.featureGroup([depot_markers[i], depot_rectangles[i]]));
                    depot_rectangles[i].depot_id = i;
                    depot_markers[i].depot_id = i;
                    depots[i].depot_id = i;
                    setLabel(i, initial_labels[i]);
                    {{this._parent.get_name()}}.addLayer(depots[i]);
                    if(i == 0)
                        highlight(i);
                    else
                        dehighlight(i);
                }
                
                var ARROWLEFT = 37; 
                var ARROWUP = 38;   
                var ARROWRIGHT = 39;
                var ARROWDOWN = 40; 
                
                var UP = 87;    //W key
                var LEFT = 65;  //A key
                var DOWN = 83;  //S key
                var RIGHT = 68; //D key
                var DELETE = 46;//DEL key
                
                var NEW = 78;   //N key
                
                var NEXT = 75;   //K key
                var PREV = 74;   //J key
                
                var PLUS = 187;   //+ key
                var MINUS = 189;  //- key
                var SPACE = 32;   //space bar
                
                function getEpsilon() {
                    var zoom = {{this._parent.get_name()}}.getZoom();
                    return 50*Math.pow(1/2,zoom);
                }

                function keyPressed(e){
                    var marker = depot_markers[selected];
                    var rectangle = depot_rectangles[selected];
                    
                    var bounds = rectangle.getBounds();
                    bounds = [  [bounds.getNorth(), bounds.getEast()],
                                [bounds.getSouth(), bounds.getWest()]
                                ];
                    switch(e.which) {
                        case ARROWUP:
                            bounds[0][0] += getEpsilon();
                            bounds[1][0] += getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            {{this._parent.get_name()}}.setView(getCenter(bounds));
                            break;
                        case ARROWDOWN:
                            bounds[0][0] -= getEpsilon();
                            bounds[1][0] -= getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            {{this._parent.get_name()}}.setView(getCenter(bounds));
                            break;
                        case ARROWLEFT:
                            bounds[0][1] -= getEpsilon();
                            bounds[1][1] -= getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            {{this._parent.get_name()}}.setView(getCenter(bounds));
                            break;
                        case ARROWRIGHT:
                            bounds[0][1] += getEpsilon();
                            bounds[1][1] += getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            {{this._parent.get_name()}}.setView(getCenter(bounds));
                            break;
                        case PLUS:
                            {{this._parent.get_name()}}.zoomIn();
                            break;
                        case MINUS:
                            {{this._parent.get_name()}}.zoomOut();
                            break;
                        case SPACE:
                            rotateRole(selected);
                            break;
                        case UP:
                            bounds[0][0] += getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            break;
                        case DOWN:
                            bounds[0][0] -= getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            break;
                        case LEFT:
                            bounds[0][1] -= getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            break;
                        case RIGHT:
                            bounds[0][1] += getEpsilon();
                            rectangle.setBounds(bounds);
                            marker.setLatLng(getCenter(bounds));
                            break;
                        case DELETE:
                            if(good <= 1)
                                break;
                            good -= 1;
                            {{this._parent.get_name()}}.removeLayer(depots[selected]);
                            depots[selected].label = 'discarded';
                            while(depots[selected].label == 'discarded') {
                                selected = (selected - 1 + depots.length) % depots.length;
                            }
                            highlight(selected);
                            break;
                        case NEXT:
                            if(good == 0)
                                break;
                            dehighlight(selected);
                            selected = (selected + 1) % depots.length;
                            while(depots[selected].label == 'discarded') {
                                selected = (selected + 1) % depots.length;
                            }
                            highlight(selected);
                            break;
                        case PREV:
                            if(good == 0)
                                break;
                            dehighlight(selected);
                            selected = (selected - 1 + depots.length) % depots.length;
                            while(depots[selected].label == 'discarded') {
                                selected = (selected - 1 + depots.length) % depots.length;
                            }
                            highlight(selected);
                            break;
                        case NEW:
                            good += 1;
                            dehighlight(selected);
                            selected = depots.length;
                            bounds[0][1] += 3*getEpsilon(); 
                            bounds[1][1] += 3*getEpsilon(); 
                            depot_rectangles.push(L.rectangle(bounds));
                            depot_markers.push(L.marker(getCenter(bounds),{draggable: true}));
                            depots.push(L.featureGroup([depot_markers[selected], 
                                                                depot_rectangles[selected]]));
                            depot_rectangles[selected].depot_id = selected;
                            depot_markers[selected].depot_id = selected;
                            setLabel(selected, "unkown");
                            depots[selected].depot_id = selected;
                            {{this._parent.get_name()}}.addLayer(depots[selected]);
                            depots[selected].on({click: selectDepot}); 
                            depot_markers[selected].on({drag: dragMarker}); 
                            depot_rectangles[selected].on({dblclick: changeRole}); 
                            depot_markers[selected].on({dblclick: changeRole}); 
                            highlight(selected);
                            break;
                    }
                    };

                function selectDepot(e) {
                    console.log("selectDepot on " + e.target.depot_id)
                    if(selected != e.target.depot_id) {
                        dehighlight(selected)                        
                        selected = e.target.depot_id;
                        highlight(selected)                        
                    }
                }
                    
                function dragMarker(e) {
                    if(selected != e.target.depot_id) {
                        dehighlight(selected)                        
                        selected = e.target.depot_id;
                        highlight(selected)                        
                    }
                    var marker = e.target;
                    var latlng = marker.getLatLng();
                    var rectangle = depot_rectangles[marker.depot_id];
                    var bounds = rectangle.getBounds();
                    bounds = [  [bounds.getNorth(), bounds.getEast()],
                                [bounds.getSouth(), bounds.getWest()]   ];
                    var height = bounds[1][0] - bounds[0][0];
                    var width = bounds[1][1] - bounds[0][1];
                    var center = [latlng.lat, latlng.lng];
                    bounds[0] = [center[0] - height/2, center[1] - width/2];
                    bounds[1] = [center[0] + height/2, center[1] + width/2];
                    rectangle.setBounds(bounds);
                }               
                
                function changeRole(e) {
                    rotateRole(e.target.depot_id);
                }
                
                document.onkeydown = keyPressed;
                
                for (var i = 0; i < depots.length; ++i) {
                    depots[i].on({click: selectDepot}); 
                    depot_markers[i].on({drag: dragMarker}); 
                    depot_rectangles[i].on({dblclick: changeRole}); 
                    depot_markers[i].on({dblclick: changeRole}); 
                }
                {{this._parent.get_name()}}.on('mouseup',function(e){
                               {{this._parent.get_name()}}.removeEventListener('mousemove');
                                  })
           
               function saveFile() {
                    var text = [];
                    for(var i=0; i< depots.length; ++i) {
                        var b = depot_rectangles[i].getBounds();
                        text.push(String(i) +  "\\t" + 
                                b.getNorth() + "\\t" + 
                                b.getSouth() + "\\t" +
                                b.getWest() +  "\\t" +
                                b.getEast() +  "\\t" +
                                depots[i].label + '\\n');
                    }
                    var blob = new Blob(text, {type: "text/plain;charset=utf-8"});
                    saveAs(blob, "{{this.account_id}}.tab");
                };
		
            {% endmacro %}
            """)  # noqa

class PolyLine(MacroElement):
    """
    Creates a PolyLine object to append into a map with
    Map.add_children.

    Parameters
    ----------
    locations: list of points (latitude, longitude)
        Latitude and Longitude of line (Northing, Easting)
    color: string, default Leaflet's default ('#03f')
    weight: float, default Leaflet's default (5)
    opacity: float, default Leaflet's default (0.5)
    latlon: bool, default True
        Whether locations are given in the form [[lat, lon]]
        or not ([[lon, lat]] if False).
        Note that the default GeoJson format is latlon=False,
        while Leaflet polyline's default is latlon=True.
    popup: string or folium.Popup, default None
        Input text or visualization for object.
    """
    def __init__(self, locations, color=None, weight=None,
                 opacity=None, latlon=True, popup=None):
        super(PolyLine, self).__init__()
        self._name = 'PolyLine'
        self.data = (_locations_mirror(locations) if not latlon else
                     _locations_tolist(locations))
        self.color = color
        self.weight = weight
        self.opacity = opacity
        if isinstance(popup, text_type) or isinstance(popup, binary_type):
            self.add_children(Popup(popup))
        elif popup is not None:
            self.add_children(popup)

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                var {{this.get_name()}} = L.polyline(
                    {{this.data}},
                    {
                        {% if this.color != None %}color: '{{ this.color }}',{% endif %}
                        {% if this.weight != None %}weight: {{ this.weight }},{% endif %}
                        {% if this.opacity != None %}opacity: {{ this.opacity }},{% endif %}
                        });
                {{this._parent.get_name()}}.addLayer({{this.get_name()}});
            {% endmacro %}
            """)  # noqa

    def _get_self_bounds(self):
        """Computes the bounds of the object itself (not including it's children)
        in the form [[lat_min, lon_min], [lat_max, lon_max]]
        """
        bounds = [[None, None], [None, None]]
        for point in iter_points(self.data):
            bounds = [
                [
                    none_min(bounds[0][0], point[0]),
                    none_min(bounds[0][1], point[1]),
                ],
                [
                    none_max(bounds[1][0], point[0]),
                    none_max(bounds[1][1], point[1]),
                ],
            ]
        return bounds


class MultiPolyLine(MacroElement):
    """
    Creates a MultiPolyLine object to append into a map with
    Map.add_children.

    Parameters
    ----------
    locations: list of points (latitude, longitude)
        Latitude and Longitude of line (Northing, Easting)
    color: string, default Leaflet's default ('#03f')
    weight: float, default Leaflet's default (5)
    opacity: float, default Leaflet's default (0.5)
    latlon: bool, default True
        Whether locations are given in the form [[lat, lon]]
        or not ([[lon, lat]] if False).
        Note that the default GeoJson format is latlon=False,
        while Leaflet polyline's default is latlon=True.
    popup: string or folium.Popup, default None
        Input text or visualization for object.
    """
    def __init__(self, locations, color=None, weight=None,
                 opacity=None, latlon=True, popup=None):
        super(MultiPolyLine, self).__init__()
        self._name = 'MultiPolyLine'
        self.data = (_locations_mirror(locations) if not latlon else
                     _locations_tolist(locations))
        self.color = color
        self.weight = weight
        self.opacity = opacity
        if isinstance(popup, text_type) or isinstance(popup, binary_type):
            self.add_children(Popup(popup))
        elif popup is not None:
            self.add_children(popup)

        self._template = Template(u"""
            {% macro script(this, kwargs) %}
                var {{this.get_name()}} = L.multiPolyline(
                    {{this.data}},
                    {
                        {% if this.color != None %}color: '{{ this.color }}',{% endif %}
                        {% if this.weight != None %}weight: {{ this.weight }},{% endif %}
                        {% if this.opacity != None %}opacity: {{ this.opacity }},{% endif %}
                        });
                {{this._parent.get_name()}}.addLayer({{this.get_name()}});
            {% endmacro %}
            """)  # noqa

    def _get_self_bounds(self):
        """Computes the bounds of the object itself (not including it's children)
        in the form [[lat_min, lon_min], [lat_max, lon_max]]
        """
        bounds = [[None, None], [None, None]]
        for point in iter_points(self.data):
            bounds = [
                [
                    none_min(bounds[0][0], point[0]),
                    none_min(bounds[0][1], point[1]),
                ],
                [
                    none_max(bounds[1][0], point[0]),
                    none_max(bounds[1][1], point[1]),
                ],
            ]
        return bounds


class CustomIcon(Icon):
    """Create a custom icon, based on an image.

    Parameters
    ----------
    icon_image :  string, file or array-like object
        The data you want to use as an icon.
        * If string, it will be written directly in the output file.
        * If file, it's content will be converted as embedded in the
        output file.
        * If array-like, it will be converted to PNG base64 string
        and embedded in the output.
    icon_size : tuple of 2 int
        Size of the icon image in pixels.
    icon_anchor : tuple of 2 int
        The coordinates of the "tip" of the icon
        (relative to its top left corner).
        The icon will be aligned so that this point is at the
        marker's geographical location.
    shadow_image :  string, file or array-like object
        The data for the shadow image. If not specified,
        no shadow image will be created.
    shadow_size : tuple of 2 int
        Size of the shadow image in pixels.
    shadow_anchor : tuple of 2 int
        The coordinates of the "tip" of the shadow relative to its
        top left corner (the same as icon_anchor if not specified).
    popup_anchor : tuple of 2 int
        The coordinates of the point from which popups will "open",
        relative to the icon anchor.
    """
    def __init__(self, icon_image, icon_size=None, icon_anchor=None,
                 shadow_image=None, shadow_size=None, shadow_anchor=None,
                 popup_anchor=None):
        super(Icon, self).__init__()
        self._name = 'CustomIcon'
        self.icon_url = image_to_url(icon_image)
        self.icon_size = icon_size
        self.icon_anchor = icon_anchor

        self.shadow_url = (image_to_url(shadow_image)
                           if shadow_image is not None else None)
        self.shadow_size = shadow_size
        self.shadow_anchor = shadow_anchor
        self.popup_anchor = popup_anchor

        self._template = Template(u"""
            {% macro script(this, kwargs) %}

                var {{this.get_name()}} = L.icon({
                    iconUrl: '{{this.icon_url}}',
                    {% if this.icon_size %}iconSize: [{{this.icon_size[0]}},{{this.icon_size[1]}}],{% endif %}
                    {% if this.icon_anchor %}iconAnchor: [{{this.icon_anchor[0]}},{{this.icon_anchor[1]}}],{% endif %}

                    {% if this.shadow_url %}shadowUrl: '{{this.shadow_url}}',{% endif %}
                    {% if this.shadow_size %}shadowSize: [{{this.shadow_size[0]}},{{this.shadow_size[1]}}],{% endif %}
                    {% if this.shadow_anchor %}shadowAnchor: [{{this.shadow_anchor[0]}},{{this.shadow_anchor[1]}}],{% endif %}

                    {% if this.popup_anchor %}popupAnchor: [{{this.popup_anchor[0]}},{{this.popup_anchor[1]}}],{% endif %}
                    });
                {{this._parent.get_name()}}.setIcon({{this.get_name()}});
            {% endmacro %}
            """)  # noqa
