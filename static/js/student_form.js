<script>
    class StudentForm {
        constructor() {
            this.currentSection = 0;
            this.sections = document.querySelectorAll('.form-section');
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.setupValidation();
            this.setupFileUploads();
            this.updateProgressBar();
            this.showSection(0);
        }

        setupEventListeners() {
            // Date of birth age calculation
            document.getElementById('id_date_of_birth').addEventListener('change', (e) => this.calculateAge(e));
            
            // Visa details toggle
            document.getElementById('id_visa_apply_record').addEventListener('change', (e) => this.toggleVisaDetails(e));
            
            // Form submission
            document.getElementById('studentForm').addEventListener('submit', (e) => this.handleSubmit(e));
            
            // Photo upload
            document.getElementById('photoContainer').addEventListener('click', () => this.triggerFileInput());
            document.getElementById('id_photo').addEventListener('change', (e) => this.handlePhotoUpload(e));
            
            // Drag and drop for photo
            this.setupDragAndDrop();
            
            // Navigation buttons if you add multi-step form
            this.setupNavigation();
        }

        setupValidation() {
            const form = document.getElementById('studentForm');
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                input.addEventListener('blur', (e) => this.validateField(e.target));
                input.addEventListener('input', (e) => this.clearError(e.target));
            });
        }

        setupFileUploads() {
            const fileInputs = document.querySelectorAll('input[type="file"]');
            fileInputs.forEach(input => {
                input.addEventListener('change', (e) => this.handleFileUpload(e));
            });
        }

        setupDragAndDrop() {
            const photoContainer = document.getElementById('photoContainer');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                photoContainer.addEventListener(eventName, this.preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                photoContainer.addEventListener(eventName, () => this.highlightArea(), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                photoContainer.addEventListener(eventName, () => this.unhighlightArea(), false);
            });

            photoContainer.addEventListener('drop', (e) => this.handleDrop(e), false);
        }

        setupNavigation() {
            // If you want to implement multi-step form navigation
            const nextBtn = document.createElement('button');
            nextBtn.type = 'button';
            nextBtn.className = 'btn btn-success';
            nextBtn.innerHTML = 'Next Section →';
            nextBtn.addEventListener('click', () => this.nextSection());

            const prevBtn = document.createElement('button');
            prevBtn.type = 'button';
            prevBtn.className = 'btn btn-secondary';
            prevBtn.innerHTML = '← Previous Section';
            prevBtn.addEventListener('click', () => this.previousSection());

            const navContainer = document.createElement('div');
            navContainer.className = 'form-navigation';
            navContainer.appendChild(prevBtn);
            navContainer.appendChild(nextBtn);

            document.querySelector('.form-container form').appendChild(navContainer);
        }

        calculateAge(e) {
            const dob = new Date(e.target.value);
            if (isNaN(dob.getTime())) return;

            const today = new Date();
            let age = today.getFullYear() - dob.getFullYear();
            const monthDiff = today.getMonth() - dob.getMonth();
            
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
                age--;
            }
            
            document.getElementById('id_age').value = age;
        }

        toggleVisaDetails(e) {
            const visaDetailsContainer = document.getElementById('visaDetailsContainer');
            if (e.target.value === 'yes') {
                visaDetailsContainer.style.display = 'flex';
                this.slideDown(visaDetailsContainer);
            } else {
                this.slideUp(visaDetailsContainer, () => {
                    visaDetailsContainer.style.display = 'none';
                });
            }
        }

        triggerFileInput() {
            document.getElementById('id_photo').click();
        }

        handlePhotoUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            if (!file.type.match('image.*')) {
                this.showError('Please select a valid image file.');
                return;
            }

            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                this.showError('Image size should be less than 5MB.');
                return;
            }

            this.displayImagePreview(file);
        }

        handleFileUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                this.showError(`File size should be less than ${maxSize / 1024 / 1024}MB.`);
                e.target.value = '';
                return;
            }

            this.showSuccess(`File "${file.name}" selected successfully.`);
        }

        displayImagePreview(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const photoContainer = document.getElementById('photoContainer');
                const photoPreview = document.getElementById('photoPreview');
                const photoPlaceholder = photoContainer.querySelector('.photo-placeholder');
                
                photoPlaceholder.style.display = 'none';
                photoPreview.src = e.target.result;
                photoPreview.style.display = 'block';
                
                this.showSuccess('Photo uploaded successfully!');
            };
            reader.readAsDataURL(file);
        }

        preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        highlightArea() {
            document.getElementById('photoContainer').classList.add('dragover');
        }

        unhighlightArea() {
            document.getElementById('photoContainer').classList.remove('dragover');
        }

        handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            document.getElementById('id_photo').files = files;
            this.handlePhotoUpload({ target: { files: files } });
        }

        validateField(field) {
            const value = field.value.trim();
            const errorElement = field.parentNode.querySelector('.error-message');

            // Clear previous error
            this.clearError(field);

            // Required field validation
            if (field.hasAttribute('required') && !value) {
                this.showFieldError(field, 'This field is required.');
                return false;
            }

            // Email validation
            if (field.type === 'email' && value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    this.showFieldError(field, 'Please enter a valid email address.');
                    return false;
                }
            }

            // Phone validation
            if (field.name === 'phone' && value) {
                const phoneRegex = /^[0-9+\-\s()]{10,}$/;
                if (!phoneRegex.test(value)) {
                    this.showFieldError(field, 'Please enter a valid phone number.');
                    return false;
                }
            }

            return true;
        }

        showFieldError(field, message) {
            field.classList.add('error');
            let errorElement = field.parentNode.querySelector('.error-message');
            
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'error-message';
                field.parentNode.appendChild(errorElement);
            }
            
            errorElement.textContent = message;
        }

        clearError(field) {
            field.classList.remove('error');
            const errorElement = field.parentNode.querySelector('.error-message');
            if (errorElement) {
                errorElement.textContent = '';
            }
        }

        async handleSubmit(e) {
            e.preventDefault();
            
            // Validate all fields
            const isValid = this.validateForm();
            
            if (!isValid) {
                this.showError('Please fix the errors in the form before submitting.');
                this.scrollToFirstError();
                return;
            }

            // Show loading state
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading"></span> Processing...';
            submitBtn.disabled = true;

            try {
                // Simulate API call or form processing
                await this.submitFormData(new FormData(e.target));
                
                this.showSuccess('Student registration submitted successfully!');
                setTimeout(() => {
                    window.location.href = "{% url 'student_list' %}";
                }, 2000);
                
            } catch (error) {
                this.showError('An error occurred while submitting the form. Please try again.');
                console.error('Form submission error:', error);
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }

        validateForm() {
            let isValid = true;
            const form = document.getElementById('studentForm');
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!this.validateField(field)) {
                    isValid = false;
                }
            });
            
            return isValid;
        }

        scrollToFirstError() {
            const firstError = document.querySelector('.error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        async submitFormData(formData) {
            // Simulate API call delay
            return new Promise((resolve) => {
                setTimeout(() => {
                    console.log('Form data:', Object.fromEntries(formData));
                    resolve();
                }, 1500);
            });
        }

        showSuccess(message) {
            this.showMessage(message, 'success');
        }

        showError(message) {
            this.showMessage(message, 'error');
        }

        showMessage(message, type) {
            // Remove existing messages
            const existingMessages = document.querySelectorAll('.alert');
            existingMessages.forEach(msg => msg.remove());

            // Create new message
            const messageDiv = document.createElement('div');
            messageDiv.className = `alert alert-${type}`;
            messageDiv.innerHTML = `
                <span>${type === 'success' ? '✓' : '⚠'}</span>
                <span>${message}</span>
            `;

            // Insert at top of form
            const form = document.getElementById('studentForm');
            form.insertBefore(messageDiv, form.firstChild);

            // Auto-remove success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.remove();
                }, 5000);
            }
        }

        // Multi-section form methods
        showSection(index) {
            this.sections.forEach((section, i) => {
                section.style.display = i === index ? 'block' : 'none';
            });
            this.currentSection = index;
            this.updateProgressBar();
        }

        nextSection() {
            if (this.currentSection < this.sections.length - 1) {
                this.showSection(this.currentSection + 1);
            }
        }

        previousSection() {
            if (this.currentSection > 0) {
                this.showSection(this.currentSection - 1);
            }
        }

        updateProgressBar() {
            const steps = document.querySelectorAll('.progress-step');
            steps.forEach((step, index) => {
                step.classList.remove('active', 'completed');
                if (index === this.currentSection) {
                    step.classList.add('active');
                } else if (index < this.currentSection) {
                    step.classList.add('completed');
                }
            });
        }

        // Animation helpers
        slideDown(element) {
            element.style.height = 'auto';
            const height = element.clientHeight + 'px';
            element.style.height = '0px';
            
            setTimeout(() => {
                element.style.height = height;
            }, 10);
        }

        slideUp(element, callback) {
            element.style.height = '0px';
            element.addEventListener('transitionend', function handler() {
                element.removeEventListener('transitionend', handler);
                if (callback) callback();
            });
        }
    }

    // Initialize the form when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
        new StudentForm();
        
        // Initialize any existing values
        const visaApplyRecord = document.getElementById('id_visa_apply_record');
        if (visaApplyRecord && visaApplyRecord.value === 'yes') {
            document.getElementById('visaDetailsContainer').style.display = 'flex';
        }
    });

    // Add progress bar HTML if you want multi-step form
    function addProgressBar() {
        const progressHTML = `
            <div class="progress-bar">
                <div class="progress-step">Personal Info</div>
                <div class="progress-step">Family & Education</div>
                <div class="progress-step">Work & Documents</div>
                <div class="progress-step">Review</div>
            </div>
        `;
        document.querySelector('.form-container').insertAdjacentHTML('afterbegin', progressHTML);
    }

    // Uncomment to enable multi-step form
    // addProgressBar();
</script>