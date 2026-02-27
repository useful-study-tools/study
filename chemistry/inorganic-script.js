function reveal(element) {
    element.classList.toggle('revealed');
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    const blanks = document.querySelectorAll('.blank-container');
    blanks.forEach(blank => {
        blank.addEventListener('mouseenter', function() {
            if (!this.classList.contains('revealed')) {
                this.style.opacity = '0.8';
            }
        });
        blank.addEventListener('mouseleave', function() {
            this.style.opacity = '1';
        });
    });
});
