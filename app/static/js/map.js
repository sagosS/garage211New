// Тут можна додати інтерактивність для карти, якщо потрібно.
// Наприклад, відкриття карти у новому вікні по кліку:
document.querySelectorAll('.footer-map iframe').forEach(iframe => {
    iframe.addEventListener('click', function() {
        window.open('https://maps.google.com/maps?q=Кривий%20Ріг&t=&z=13&ie=UTF8&iwloc=&output=embed', '_blank');
    });
});