<div id='loadingText'>
    Please wait while we load your strava data...
</div>

<script>
    const urlParams = new URLSearchParams(window.location.search);
    let page = urlParams.get('page') ? parseInt(urlParams.get('page')) : 0;

    window.location.replace("/preload?page=" + (page + 1));

    const loadingTextElement = document.getElementById('loadingText');
    const trimmedText = loadingTextElement.textContent.trim();
    loadingTextElement.textContent = trimmedText + '.'.repeat(page);
</script>
