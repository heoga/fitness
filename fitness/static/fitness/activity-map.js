function create_map(url) {
    console.log('Loading activity map from ', url);
    $.getJSON(url + "?format=json",
    function(data) {
        var Thunderforest_Outdoors = L.tileLayer(
            'http://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 22
        });
        mapnik = L.tileLayer.provider('OpenStreetMap.Mapnik');
        cartoDark = L.tileLayer.provider('CartoDB.DarkMatter');

        var activity_map = L.map('map', {
            center: [0, 0],
            zoom: 15,
            layers: [cartoDark]
        });

        var baseMaps = {
            "Carto Dark": cartoDark,
            "Landscape": Thunderforest_Outdoors,
            "Mapnik": mapnik,
        };
        L.control.layers(baseMaps).addTo(activity_map);
        console.log(data.track);
        console.log(activity_map);
        L.polyline(data.track, { className: 'activity-polyline' }).addTo(activity_map);
        activity_map.fitBounds(data.track);
    });
}
