// skycons
var weather_icon = $('#dust-weather').data('icon');
var skycons = new Skycons({'color': '#eee'});
skycons.add("dust-weather", Skycons[weather_icon]);
skycons.add("dust-weather-day-1", Skycons[weather_icon]);
skycons.add("dust-weather-day-2", Skycons[weather_icon]);
skycons.add("dust-weather-day-3", Skycons[weather_icon]);
skycons.add("dust-weather-day-4", Skycons[weather_icon]);
skycons.add("dust-weather-day-5", Skycons[weather_icon]);
skycons.add("dust-weather-day-6", Skycons[weather_icon]);
skycons.play();

// momentjs
window.setInterval(update_time, 15000);

function update_time(tag) {
  if (tag)
    $(tag).text(moment().format('LTS'));
  else
    $('#dust-current-time').text(moment().format('LTS'));
}

update_time('#dust-last-updated');
update_time();

// morris
new Morris.Line({
  // ID of the element in which to draw the chart.
  element: 'ijichart',
  // Chart data records -- each entry in this array corresponds to a point on
  // the chart.
  data: [
    { date: '1', value: 250 },
    { date: '2', value: 10 },
    { date: '3', value: 5 },
    { date: '4', value: 40 },
    { date: '5', value: 200 }
  ],
  // The name of the data record attribute that contains x-values.
  xkey: 'date',
  // A list of names of data record attributes that contain y-values.
  ykeys: ['value'],
  // Labels for the ykeys -- will be displayed when you hover over the
  // chart.
  labels: [''],
  lineColors: '7f8c8d',
  pointSize: 4,
  pointStrokeColors: 'black',
  hideHover: true,
  axes: false,
  grid: false,
  postUnits: 'MB',
  yLabelFormat: function(y) { return y.toString() + ' MB' }
});

$(function() {
  $('.grid').masonry({
    itemSelector: '.dust-grid'
  });
});
/*
 * vim:ts=2:sts=2:sw=2:et
 */
