<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>3thirty Charts for Strava</title>
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

      body {
        margin: 0;
        font-family: 'Quicksand', sans-serif;
        background-color: #fcf4e4;
        color: #333;
      }

      main.container {
        flex: 1;
        padding: 60px 20px 40px;
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
        max-width: 1200px;
        margin: 0 auto;
      }

      .container {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        padding: 60px 20px 100px;
        max-width: 1200px;
        margin: 0 auto;
        flex-wrap: wrap;
      }

      .hero-img {
        max-width: 400px;
        width: 100%;
      }

      .text-content {
        max-width: 600px;
        padding: 20px;
        text-align: left;
      }

    h1 {
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: #e87722;
    }

    h2 {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 1rem;
    }

    p {
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 2rem;
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
    </style>
  </head>
  <body>
    <main class="container">
      <img
        src="https://stravacharts.3thirty.space/assets/spacekitty.png"
        alt="Cat astronaut on a bike"
        class="hero-img"
      />
      <div class="text-content">
        <h1 id="loadingText">Loading...</h1>
        <h2>Downloading your workouts from strava</h2>
      </div>
    </main>
    <footer>
      <a href="https://www.3thirty.net">
        <img src="assets/clock.jpg" alt="clock icon" class="footer-icon">3thirty
      </a>
      <a href="https://www.github.com/3thirty/strava_charts">
        <img src="assets/github.png" alt="clock icon" class="footer-icon">GitHub
      </a>
      <a href="mailto:ethan@3thirty.net">✉️ Contact</a>
    </footer>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        let page = urlParams.get('page') ? parseInt(urlParams.get('page')) : 0;
    
        document.getElementById('loadingText').textContent += ".".repeat(page);
    
        window.location.replace("/preload?page=" + (page + 1));
    </script>
  </body>
</html>
