document.addEventListener('DOMContentLoaded', function() {
    // Координати вашого гаража (числові значення!)
    const lat = 47.901460;
    const lon = 33.299943;

    // Відображення карти
    var map = L.map('footer-map', {
        scrollWheelZoom: false,
        dragging: window.innerWidth > 600, // Дозволити drag тільки на десктопі
        zoomControl: false,
        tap: false
    }).setView([lat, lon], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    L.marker([lat, lon]).addTo(map);

    // Відкриття маршруту (iOS/Android/desktop)
    document.getElementById('footer-route-btn').addEventListener('click', function(e) {
        e.preventDefault();
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isAndroid = /Android/.test(navigator.userAgent);
        let url = '';
        if (isIOS) {
            url = `maps://maps.apple.com/?daddr=${lat},${lon}`;
        } else if (isAndroid) {
            url = `geo:${lat},${lon}?q=${lat},${lon}`;
        } else {
            url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&travelmode=driving&dir_action=navigate`;
            // url = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${lat},${lon}`;
        }
        window.open(url, '_blank');
    });
});