// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.server-card, .feature-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, { threshold: 0.1 });

    cards.forEach(card => {
        observer.observe(card);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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

    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.type === 'submit' || this.classList.contains('loading-btn')) {
                this.style.position = 'relative';
                this.style.pointerEvents = 'none';
                
                const originalContent = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                
                // Reset after 3 seconds if no form submission
                setTimeout(() => {
                    if (this.innerHTML.includes('Loading...')) {
                        this.innerHTML = originalContent;
                        this.style.pointerEvents = 'auto';
                    }
                }, 3000);
            }
        });
    });

    // Enhanced mobile navigation
    const navTabs = document.querySelector('.nav-tabs');
    if (navTabs && window.innerWidth <= 768) {
        navTabs.style.display = 'none';
        
        const toggleBtn = document.createElement('button');
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        toggleBtn.className = 'nav-toggle';
        toggleBtn.style.cssText = `
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 1.2rem;
            padding: 0.5rem;
            cursor: pointer;
            border-radius: 4px;
            transition: var(--transition);
        `;
        
        document.querySelector('.nav-container').appendChild(toggleBtn);
        
        toggleBtn.addEventListener('click', () => {
            const isVisible = navTabs.style.display !== 'none';
            navTabs.style.display = isVisible ? 'none' : 'flex';
            toggleBtn.innerHTML = isVisible ? '<i class="fas fa-bars"></i>' : '<i class="fas fa-times"></i>';
        });
    }
});
