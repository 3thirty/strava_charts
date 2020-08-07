<html>

<head>
    <title>Strava Power Over Time</title>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.min.js"></script>
</head>

<body>

<div style="width: 80%">
    <canvas id="chart"></canvas>
</div>

<script>
    var ctx = document.getElementById("chart").getContext('2d');
    var data = {{ !chartJSON }}
    var myChart = new Chart(ctx, data);
</script>

</body>
</html>
