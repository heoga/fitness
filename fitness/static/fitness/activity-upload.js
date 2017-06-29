parsedActivities = {}
readStatus = {
    input: 0,
    output: 0,
    allInput: false,
    parsedActivities: {},
    count: 0,
    uploaded: 0
}
function calculateDistance(lat1, lon1, lat2, lon2, unit) {
	var radlat1 = Math.PI * lat1/180
	var radlat2 = Math.PI * lat2/180
	var theta = lon1-lon2
	var radtheta = Math.PI * theta/180
	var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
	dist = Math.acos(dist)
	dist = dist * 180/Math.PI
	dist = dist * 60 * 1.1515
	if (unit=="K") { dist = dist * 1.609344 }
	if (unit=="m") { dist = dist * 1609.344 }
	if (unit=="N") { dist = dist * 0.8684 }
	return dist
}
function readMultipleTCX(evt){
    readStatus.input = 0;
    readStatus.output = 0;
    readStatus.allInput = false;
    readStatus.parsedActivities = {};
    $.each(evt.target.files, function(index, file) {
        readStatus.input += 1;
        reader = new FileReader();
        reader.addEventListener("load", readTCXText, false);
        reader.readAsText(file);
    });
    readStatus.allInput = true;
}
function readMultipleGPX(evt){
    clearStatus();
    $.each(evt.target.files, function(index, file) {
        readStatus.input += 1;
        reader = new FileReader();
        reader.addEventListener("load", readGPXText, false);
        reader.readAsText(file);
    });
    readStatus.allInput = true;
}
function readTCXText(event) {
    var text = event.target.result;
    var parser = new DOMParser()
    var xml = parser.parseFromString(text, "text/xml")
    var activities = xml.getElementsByTagName("Activity");
    $.each(activities, function(index, activity) {
        if (activity.attributes.Sport.nodeValue == "Running") {
            var currentActivity = {}
            currentActivity.time = activity.getElementsByTagName("Id")[0].innerHTML;
            currentActivity.name = activity.getElementsByTagName("Notes")[0].innerHTML;
            currentActivity.points = [];
            $.each(activity.getElementsByTagName("Trackpoint"), function(index, trackpoint) {
                var parsedPoint = {};
                var time = trackpoint.getElementsByTagName("Time")[0];
                var altitude = trackpoint.getElementsByTagName("AltitudeMeters")[0];
                var distance = trackpoint.getElementsByTagName("DistanceMeters")[0];
                var latitude = trackpoint.getElementsByTagName("LatitudeDegrees")[0];
                var longitude = trackpoint.getElementsByTagName("LongitudeDegrees")[0];
                var cadence = trackpoint.getElementsByTagName("RunCadence")[0];
                var speed = trackpoint.getElementsByTagName("Speed")[0];
                var heartRate = trackpoint.getElementsByTagName("HeartRateBpm")[0];

                if (time && altitude && distance && latitude && longitude) {
                    parsedPoint.time = time.innerHTML;
                    parsedPoint.altitude = parseFloat(altitude.innerHTML);
                    parsedPoint.distance = parseFloat(distance.innerHTML);
                    parsedPoint.latitude = parseFloat(latitude.innerHTML);
                    parsedPoint.longitude = parseFloat(longitude.innerHTML);
                } else {
                    return;
                }

                if (cadence) {
                    parsedPoint.cadence = parseFloat(cadence.innerHTML);
                } else {
                    parsedPoint.cadence = null;
                }
                if (speed) {
                    parsedPoint.speed = parseFloat(speed.innerHTML);
                } else {
                    parsedPoint.speed = null;
                }
                if (heartRate) {
                    parsedPoint.heart_rate = parseFloat(heartRate.getElementsByTagName("Value")[0].innerHTML);
                } else {
                    parsedPoint.heart_rate = null;
                }
                currentActivity.points.push(parsedPoint);
            });
            if (Object.keys(currentActivity.points).length > 0) {
                readStatus.parsedActivities[currentActivity.time] = currentActivity;
            }
        }
    });
    readStatus.output += 1;
    updateReadStatus();
    if (readStatus.input == readStatus.output) {
        readComplete();
    }
}
function readGPXText(event) {
    var text = event.target.result;
    var parser = new DOMParser()
    var xml = parser.parseFromString(text, "text/xml")
    var activities = xml.getElementsByTagName("trk");
    $.each(activities, function(index, activity) {
        var trackType = activity.getElementsByTagName("type")[0]
        if (!trackType || trackType.innerHTML == "running") {
            var currentActivity = {}
            var previousLatitude = null;
            var previousLongitude = null;
            var previousTime = null;
            var previousDistance = 0;
            currentActivity.name = activity.getElementsByTagName("name")[0].innerHTML;
            currentActivity.points = [];
            $.each(activity.getElementsByTagName("trkpt"), function(index, trackpoint) {
                var parsedPoint = {};
                var time = trackpoint.getElementsByTagName("time")[0].innerHTML;
                var altitude = trackpoint.getElementsByTagName("ele")[0];
                var latitude = trackpoint.attributes.lat.nodeValue;
                var longitude = trackpoint.attributes.lon.nodeValue;
                var cadence = trackpoint.getElementsByTagName("ns3:cad")[0];
                var heartRate = trackpoint.getElementsByTagName("ns3:hr")[0];
                if (time && altitude && latitude && longitude) {
                    parsedPoint.time = time;
                    parsedPoint.altitude = parseFloat(altitude.innerHTML);
                    parsedPoint.latitude = parseFloat(latitude);
                    parsedPoint.longitude = parseFloat(longitude);
                } else {
                    return;
                }
                // Calculate Distance.
                if (previousLatitude && previousLongitude) {
                    var distanceIncrement = calculateDistance(previousLatitude, previousLongitude, latitude, longitude, 'm');
                    parsedPoint.distance = previousDistance + distanceIncrement;
                } else {
                    parsedPoint.distance = 0.0;
                    var distanceIncrement = 0;
                }
                previousLatitude = latitude;
                previousLongitude = longitude;
                previousDistance = parsedPoint.distance;
                // Calculate Speed.
                newTime = new Date(time);
                if (previousTime) {
                    var seconds = (newTime - previousTime) / 1000;
                    parsedPoint.speed = distanceIncrement / seconds;
                }
                else {
                    parsedPoint.speed = 0.0;
                }
                previousTime = new Date(time);
                if (cadence) {
                    parsedPoint.cadence = parseFloat(cadence.innerHTML);
                } else {
                    parsedPoint.cadence = null;
                }
                if (heartRate) {
                    parsedPoint.heart_rate = parseFloat(heartRate.innerHTML);
                } else {
                    parsedPoint.heart_rate = null;
                }
                currentActivity.points.push(parsedPoint);
                if (!currentActivity.time) {
                    currentActivity.time = parsedPoint.time;
                }
            });
            if (Object.keys(currentActivity.points).length > 0) {
                readStatus.parsedActivities[currentActivity.time] = currentActivity;
            }
        }
    });
    readStatus.output += 1;
    updateReadStatus();
    if (readStatus.input == readStatus.output) {
        readComplete();
    }
}
function updateReadStatus() {
    var runCount = Object.keys(readStatus.parsedActivities).length;
    readStatus.count = runCount;
    $("#readStatus").html("Read " + readStatus.output + " of " + readStatus.input + " files. Found " + runCount + " runs.");
};

function labelFromTime(time) {
    var response = time.replace(/:/g, '').replace(/-/g, '').replace(/\./g, '');
    return response;
}

function readComplete() {
    var layers = [];
    $.each(readStatus.parsedActivities, function(index, activity) {
        var display_date = new Date(activity.time);
        layers.push(
            '<div class="panel panel-default" id="' + labelFromTime(activity.time) + '">' +
            '  <div class="panel-heading">' +
            '    <h3 class="panel-title">' + display_date + '</h3>' +
            '  </div>' +
            '  <div class="panel-body">' + activity.name +
            '  </div>' +
            '</div>'
        );
    });
    $("#located_runs").html(layers.join(' '));
    $("#upload").prop('disabled', false);
}
function clearStatus(){
    readStatus.input = 0;
    readStatus.output = 0;
    readStatus.allInput = false;
    readStatus.parsedActivities = {};
    $("#located_runs").html('');
    $("#readStatus").html('');
    $("#upload").prop('disabled', true);
    $("#progress").prop("hidden", true);
}
function clearStatusEvent(event){
    clearStatus();
}
function uploadActivities(){
    $.each(readStatus.parsedActivities, function(index, activity) {
        $.ajax({
            url:"/fitness/api/activities/",
            type:"POST",
            data: JSON.stringify(activity),
            contentType:"application/json; charset=utf-8",
            dataType:"json",
            success: function(){
                var id = JSON.parse(this.data).time;
                var panel = $("#" + labelFromTime(id));
                panel.removeClass('panel-default');
                panel.addClass('panel-success');
                readStatus.uploaded++;
                var percentDone = Math.min(100, Math.floor(100 * (readStatus.uploaded / readStatus.count)));
                $("#progress").css('width', percentDone + '%').attr("aria-valuenow", percentDone);
                $("#progress").html(percentDone + '%');
                $("#progress").prop("hidden", false);

            }
        }).fail(function(XMLHttpRequest, textStatus, errorThrown){
            var id = JSON.parse(this.data).time;
            var panel = $("#" + labelFromTime(id));
            panel.removeClass('panel-default');
            panel.addClass('panel-danger');
        });
    });
}