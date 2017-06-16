/*geoJsonData = [{
    "type": "Feature",
    "properties": {
        "id": 0,
        "elevation": 50,
        "pace": 25,
        "distance": 1,
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [11.836395263671875, 47.75317468890147], // longitude, latitude.
            [11.865234375, 47.73193447949174]
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": 1,
        "elevation": 750,
        "pace": 10,
        "distance": 2,
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [11.865234375, 47.73193447949174],
            [11.881027221679688, 47.700520033704954]
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": 2,
        "elevation": 1700,
        "pace": 20,
        "distance": 3,
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [11.881027221679688, 47.700520033704954],
            [11.923599243164062, 47.706527200903395]
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": 3,
        "elevation": 3000,
        "pace": 15,
        "distance": 4,
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [11.923599243164062, 47.706527200903395],
            [11.881027221679688, 47.700520033704954],
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": "progress",
    },
    "geometry": {
        "type": "Point",
        "coordinates": [
            11.836395263671875, 47.75317468890147 // longitude, latitude.
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": "start",
    },
    "geometry": {
        "type": "Point",
        "coordinates": [
            11.836395263671875, 47.75317468890147 // longitude, latitude.
        ]
    }
}, {
    "type": "Feature",
    "properties": {
        "id": "stop",
    },
    "geometry": {
        "type": "Point",
        "coordinates": [
            11.923599243164062, 47.706527200903395 // longitude, latitude.
        ]
    }
}];*/

function geoJsonToChart(field) {
    var output_data = [];
    for (var i = 0; i < geoJsonData.length; i++) {
        var item = geoJsonData[i];
        if (item.geometry.type != "LineString") {
            continue;
        }
        output_data.push({
            x: item.properties.distance,
            y: item.properties[field]
        });
    }
    return output_data
}

function geoJsonPointById(id) {
    for (var i = 0; i < geoJsonData.length; i++) {
        var item = geoJsonData[i];
        console.log(id, item, item.properties.id);
        if (item.properties.id == id) {
            return item
        }
    }
}

function geoJsonFields() {
    var fields = [];
    for (var i = 0; i < geoJsonData.length; i++) {
        var item = geoJsonData[i];
        if (item.geometry.type = "LineString") {
            for (var key in item.properties) {
                if (key.toLowerCase() == "id" || key == "distance") {
                    continue;
                }
                fields.push(key);
            }
            return fields;
        }
    }
}

function geoJsonPropertyBounds(tag) {
    var output_data = {
        max: -99999999,
        min: 99999999,
        range: 0
    };
    for (var i = 0; i < geoJsonData.length; i++) {
        var item = geoJsonData[i];
        if (item.geometry.type != "LineString") {
            continue;
        }
        var value = item.properties[tag];
        if (value > output_data.max) {
            output_data.max = value;
        }
        if (value < output_data.min) {
            output_data.min = value;
        }
    }
    output_data.range = output_data.max - output_data.min
    return output_data

}

function geoLayerById(line, id) {
    for (var index in line._layers) {
        var item = line._layers[index]
        if (item.feature.properties.id == id) {
            return item
        }
    }
}

function getColor(feature, tag) {
    if (feature.geometry.type == "Point") {
        return '#000000'
    }
    var lineValue = feature.properties[tag];
    var bounds = geoJsonPropertyBounds(tag);
    return (
        lineValue < bounds.min + 0.1 * bounds.range ? '#00e5c4' :
        lineValue < bounds.min + 0.2 * bounds.range ? '#00e075' :
        lineValue < bounds.min + 0.3 * bounds.range ? '#00dc29' :
        lineValue < bounds.min + 0.4 * bounds.range ? '#1ed800' :
        lineValue < bounds.min + 0.5 * bounds.range ? '#65d400' :
        lineValue < bounds.min + 0.6 * bounds.range ? '#a8cf00' :
        lineValue < bounds.min + 0.7 * bounds.range ? '#cbae00' :
        lineValue < bounds.min + 0.8 * bounds.range ? '#c76800' :
        lineValue < bounds.min + 0.9 * bounds.range ? '#c32500' :
        '#bf001b'
    );
};

function createLine(feature) {
    return {
        "color": getColor(feature, key),
        "opacity": 1,
    }
}

function pace(feature) {
    return {
        "color": getColor(feature, 'pace'),
        "opacity": 1,
    }
}

function markerColor(feature) {
    switch (feature.properties.id) {
        case 'start':
            return "green";
        case 'stop':
            return "red";
        case 'progress':
            return "blue";
    }
}

function pointToLayer(feature, latlng) {
    return L.circleMarker(latlng, {
        radius: 5,
        fillColor: markerColor(feature),
        color: markerColor(feature),
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    });
}

function toTitleCase(str) {
    return str.replace(/(?:^|\s)\w/g, function(match) {
        return match.toUpperCase();
    });
}

function routeLines() {
    var fields = geoJsonFields();
    console.log(fields);
    var object_data = {};
    for (var i = 0; i < fields.length; i++) {
        key = fields[i];
        console.log('From Route', key);
        object_data[toTitleCase(key)] = L.geoJson(geoJsonData, {
            style: createLine,
            pointToLayer: pointToLayer
        });
    }
    console.log(object_data);
    return object_data;
}

function generateMap() {
    // Create Map
    var displayMap = L.map('map');
    var cartoLight = L.tileLayer.provider('CartoDB.Positron');
    var cartoDark = L.tileLayer.provider('CartoDB.DarkMatter');
    var baseLayers = {
        "Light": cartoLight,
        "Dark": cartoDark
    }

    routeGeoJsons = routeLines();
    var groupedOverlays = {
        "Route": routeGeoJsons
    };
    L.control.groupedLayers(baseLayers, groupedOverlays, {
        exclusiveGroups: ["Route"],
    }).addTo(displayMap);
    cartoDark.addTo(displayMap);
    for (var routeLine in routeGeoJsons) {
        routeGeoJsons[routeLine].addTo(displayMap);
        displayMap.fitBounds(routeGeoJsons[routeLine].getBounds());
        break;
    }
    return groupedOverlays
}

function hoverChart(x) {
    if (!x[0]) {
        return
    }
    if (!x[0]._index) {
        return
    }
    var targetCoords = geoJsonPointById(x[0]._index).geometry.coordinates[0];
    for (var routeLine in routeGeoJsons) {
        var marker = geoLayerById(routeGeoJsons[routeLine], 'progress');
        marker.setLatLng([targetCoords[1], targetCoords[0]]);
    }
}

function getRandColor(brightness) {
    // Six levels of brightness from 0 to 5, 0 being the darkest
    var rgb = [Math.random() * 256, Math.random() * 256, Math.random() * 256];
    var mix = [brightness * 51, brightness * 51, brightness * 51]; //51 => 255/5
    var mixedrgb = [rgb[0] + mix[0], rgb[1] + mix[1], rgb[2] + mix[2]].map(function(x) {
        return Math.round(x / 2.0)
    })
    return "rgb(" + mixedrgb.join(",") + ")";
}

function shadeRGBColor(color, percent) {
    var f = color.split(","),
        t = percent < 0 ? 0 : 255,
        p = percent < 0 ? percent * -1 : percent,
        R = parseInt(f[0].slice(4)),
        G = parseInt(f[1]),
        B = parseInt(f[2]);
    return "rgba(" + (Math.round((t - R) * p) + R) + "," + (Math.round((t - G) * p) + G) + "," + (Math.round((t - B) * p) + B) + ", 0.5)";
}

function chartDataSets() {
    var fields = geoJsonFields();
    var chartData = {
        'dataset': [],
        'yAxes': [],
    };
    for (var i = 0; i < fields.length; i++) {
        key = fields[i];
        var title_key = toTitleCase(key);
        base_colour = getRandColor(2);
        chartData.dataset.push({
            label: title_key,
            data: geoJsonToChart(key),
            yAxisID: key + '-axis',
            borderColor: base_colour,
            backgroundColor: shadeRGBColor(base_colour, 0.5)
        })
        field_axis = {
            id: key + '-axis',
            type: 'linear',
            position: ( i & 1 ) ? "right" : "left",
            scaleLabel: {
                display: true,
                labelString: title_key
            }
        };
        if (key == 'pace' || key == 'speed') {
            field_axis['ticks'] = {
                // Include a dollar sign in the ticks
                callback: function(value, index, values) {
                    seconds_km = 1000 / value
                    min_km = Math.floor(seconds_km / 60)
                    left_over_seconds = Math.floor(seconds_km - (min_km * 60))
                    return min_km + ':' + left_over_seconds
                }
            }
        }
        chartData.yAxes.push(field_axis);
    }
    return chartData
}

function constructView(activityURL){
    console.log('Loading activity map from ', activityURL);
    $.getJSON(activityURL + "?format=json",
    function(data) {
        geoJsonData = data.geo_json;
        console.log(geoJsonData);
        generateMap();
        var ctx = document.getElementById("myChart");
        chartData = chartDataSets();
        var maxX = 0;
        var distances = geoJsonToChart('distance');
        console.log
        for (var i=0; i < distances.length; i++){
            if (distances[i].x > maxX) {
                maxX = distances[i].x;
            }
        }
        console.log(chartData, maxX);
        var scatterChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: chartData.dataset
            },
            options: {
                //responsive: false,
                intersect: false,
                scales: {
                    xAxes: [{
                        type: 'linear',
                        position: 'bottom',
                        scaleLabel: {
                            display: true,
                            labelString: 'Distance'
                        },
                        ticks: {
                            // Include a dollar sign in the ticks
                            callback: function(value, index, values) {
                                return (value / 1000).toFixed(2);
                            },
                            max: maxX
                        }
                    }],
                    yAxes: chartData.yAxes
                },
                hover: {
                    mode: 'index',
                    intersect: false,
                    onHover: hoverChart,
                },
            }
        });
    });
}
