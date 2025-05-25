window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 30) {
                navbar.classList.add('navbar-transparent');
            } else {
                navbar.classList.remove('navbar-transparent');
            }
        });