<html>

<head>
    <title>Strava Power Over Time</title>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.min.js"></script>

    <link rel="apple-touch-icon" sizes="180x180" href="/favico/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/favico/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favico/favicon-16x16.png">
    <link rel="manifest" href="favico/site.webmanifest">
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
