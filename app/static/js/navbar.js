// ...existing code...
window.addEventListener('scroll', function() {
  const navbar = document.querySelector('.navbar');
  if (window.scrollY > 10) {
    navbar.style.background = 'rgba(30,30,30,0.95)';
  } else {
    navbar.style.background = 'rgba(30,30,30,0.3)';
  }
});
// ...existing code...