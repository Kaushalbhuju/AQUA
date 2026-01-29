// static/appointment/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        }, 5000);
    });
    
    // Slot selection enhancement
    const slotCards = document.querySelectorAll('.slot-card[data-slot-id]');
    slotCards.forEach(card => {
        card.addEventListener('click', function() {
            const slotId = this.getAttribute('data-slot-id');
            const isAvailable = !this.classList.contains('booked');
            
            if (isAvailable) {
                // Remove selected class from all cards
                slotCards.forEach(c => c.classList.remove('selected'));
                
                // Add selected class to clicked card
                this.classList.add('selected');
                
                // Update hidden input if exists
                const slotInput = document.querySelector('input[name="appointment_slot"]');
                if (slotInput) {
                    slotInput.value = slotId;
                }
            }
        });
    });
    
    // Real-time validation for phone number
    const phoneInput = document.getElementById('id_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (this.value && !phoneRegex.test(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
});