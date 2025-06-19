<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>3thirty Charts for Strava</title>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.min.js"></script>
  
  <link rel="apple-touch-icon" sizes="180x180" href="/favico/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/favico/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favico/favicon-16x16.png">
  <link rel="manifest" href="favico/site.webmanifest">

  <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap" rel="stylesheet">
  <style>
    html, body {
        height: 100%;
        margin: 0;
        font-family: 'Quicksand', sans-serif;
        background-color: #fcf4e4;
        display: flex;
        flex-direction: column;
      }

    header {
      padding: 40px 20px 20px;
      text-align: center;
    }

    h1 {
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: #e87722; /* Warmer bolder orange tone */
    }

    header h2 {
      font-size: 1.2rem;
      font-weight: 400;
      color: #555;
      margin-bottom: 30px;
    }

    .filters {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 20px;
      margin-bottom: 40px;
    }

    .filter-group {
      display: flex;
      flex-direction: column;
      font-weight: 600;
      font-size: 0.95rem;
    }

    .filter-group label {
      margin-bottom: 6px;
    }

    .filter-group select {
      padding: 8px 12px;
      padding-right: 36px; /* space for arrow */
      font-size: 1rem;
      border-radius: 8px;
      border: 1px solid #ccc;
      background-color: #fff;
      background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="%23999"><path d="M5.5 7l4.5 5 4.5-5z"/></svg>');
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 16px;
      appearance: none;
      -webkit-appearance: none;
      -moz-appearance: none;
      cursor: pointer;
      box-sizing: border-box;
    }

    main {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 20px 40px;
    }

    .chart-container {
      background: #fff;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      max-width: 900px;
      width: 100%;
    }

    .chart-title {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 20px;
      text-align: center;
      color: #333;
    }

    .fake-chart {
      width: 100%;
      height: 300px;
      background: repeating-linear-gradient(
        to right,
        #f8f1e8 0,
        #f8f1e8 1px,
        transparent 1px,
        transparent 40px
      ),
      repeating-linear-gradient(
        to bottom,
        #f8f1e8 0,
        #f8f1e8 1px,
        transparent 1px,
        transparent 40px
      );
      position: relative;
    }

    .fake-line {
      position: absolute;
      top: 50%;
      left: 0;
      height: 2px;
      width: 100%;
      background: #e87722;
      transform: translateY(-50%);
    }

    .button {
      margin-top: 25px;
      padding: 8px 16px;
      background-color: #ccc;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      display: inline-block;
      font-size: 0.95rem;
      transition: background 0.2s ease;
    }

    .button:hover {
      background-color: #bbb;
    }

    footer {
      background-color: #f1e9d3;
      padding: 10px 20px;
      display: flex;
      justify-content: center;
      gap: 1.5rem;
      font-size: 0.875rem;
      font-weight: bold;
    }

    footer a {
      text-decoration: none;
      color: #777;
    }

    footer a:hover {
      text-decoration: underline;
    }

    .footer-icon {
      width: 20px;
      height: 20px;
      object-fit: contain;
      vertical-align: middle;
      display: inline-block;
      margin-right: 6px;
      transform: translateY(-1px);
    }

    .stravabadge {
      max-width: auto;
      max-height: 25px;
    }

    .activity-toggle {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }

    .activity-btn {
      padding: 10px 18px;
      border: none;
      border-radius: 20px;
      background-color: #eee;
      color: #333;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s ease, transform 0.2s ease;
      font-family: 'Quicksand', sans-serif;
    }

    .activity-btn:hover {
      background-color: #ddd;
      transform: translateY(-1px);
    }

    .activity-btn.active {
      background-color: #e87722;
      color: #fff;
    }
  </style>
</head>

<body>

  <header>
    <h1>3thirty Charts for Strava</h1>
    <h2>Turn workouts into trends with time-based performance insights</h2>
  </header>

  <div class="activity-toggle">
    <button class="activity-btn active" data-activity="run">🏃 Run</button>
    <button class="activity-btn" data-activity="ride">🚴 Ride</button>
    <button class="activity-btn" data-activity="walk">🚶 Walk</button>
  </div>

  <script>
    document.addEventListener("DOMContentLoaded", () => {
      const activityButtons = document.querySelectorAll('.activity-btn');

      activityButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          activityButtons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          const selectedActivity = btn.dataset.activity;
          // TODO: update metric dropdown based on selectedActivity
        });
      });
    });
  </script>

  <div class="filters">
  <div class="filter-group">
    <label for="type">Type</label>
    <select id="type">
      <option value="average">Average</option>
      <option value="total">Total</option>
    </select>
  </div>
  <div class="filter-group">
    <label for="metric">Metric</label>
    <select id="metric">
      <option value="average_watts">Average Watts</option>
      <option value="distance">Distance</option>
      <option value="total_elevation_gain">Elevation Gain</option>
    </select>
  </div>
  <div class="filter-group">
    <label for="period">Period</label>
    <select id="period">
      <option value="week">Week</option>
      <option value="month">Month</option>
      <option value="year">Year</option>
    </select>
  </div>

  <button class="button" id="updateBtn">Update</button>

  <script>
    // set HTML elements to match the current path
    const [currentType, currentMetric, currentPeriod] = window.location.pathname.split('/').slice(2)
    document.getElementById("type").value = currentType;
    document.getElementById("metric").value = currentMetric;
    document.getElementById("period").value = currentPeriod;

    const urlParams = new URLSearchParams(window.location.search);
    const currentSport = urlParams.get('sport');

    if (currentSport) {
      const activeBtn = document.querySelector(`.activity-btn[data-activity="${currentSport}"]`);
      if (activeBtn) {
        document.querySelectorAll('.activity-btn').forEach(b => b.classList.remove('active'));
        activeBtn.classList.add('active');
      }
    }

    // change the view when the button is clicked
    document.getElementById("updateBtn").addEventListener("click", () => {
      const type = document.getElementById("type").value;
      const metric = document.getElementById("metric").value;
      const period = document.getElementById("period").value;

      const sport = document.querySelector('.activity-btn.active')?.dataset.activity;
      const query_string = sport ? `?sport=${sport}` : ''

      const basePath = window.location.pathname.split('/').slice(0, 2).join('/');
  
      const path = `${basePath}/${type}/${metric}/${period}${query_string}`;
      window.location.href = path;
    });
  </script>
</div>

  <main>
    <div class="chart-container">
        <canvas id="chart"></canvas>
    </div>

   <!-- <button class="button">Log out</button> -->
  </main>

  <footer>
    <a href="https://www.3thirty.net">
      <img src="/assets/clock.jpg" alt="clock icon" class="footer-icon">3thirty
    </a>
    <a href="https://www.github.com/3thirty/strava_charts">
      <img src="/assets/github.png" alt="clock icon" class="footer-icon">GitHub
    </a>
    <a href="mailto:ethan@3thirty.net">✉️ Contact</a>

    <a href="https://www.strava.com"><img class="stravabadge" src="/assets/powered_by_strava.png" alt="Powered by Strava"></a>
  </footer>

<script>
    var ctx = document.getElementById("chart").getContext('2d');
    var data = {{ !chartJSON }}
    var myChart = new Chart(ctx, data);
</script>

</body>
</html>
