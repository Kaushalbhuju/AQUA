document.addEventListener('DOMContentLoaded', function () {
    const steps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const finalSubmitBtn = document.getElementById('finalSubmitBtn');
    let currentStep = 0;

    updateStepDisplay();

    nextBtn.addEventListener('click', function () {
        if (validateStep(currentStep)) {
            currentStep++;
            updateStepDisplay();
        }
    });
    prevBtn.addEventListener('click', function () {
        currentStep--;
        updateStepDisplay();
    });

    function updateStepDisplay() {
        steps.forEach(step => step.classList.remove('active'));
        progressSteps.forEach(step => step.classList.remove('active'));
        steps[currentStep].classList.add('active');
        progressSteps[currentStep].classList.add('active');
        prevBtn.style.display = currentStep === 0 ? 'none' : 'inline-flex';
        nextBtn.style.display = currentStep === steps.length - 1 ? 'none' : 'inline-flex';
        submitBtn.style.display = currentStep === steps.length - 1 ? 'inline-flex' : 'none';
        progressSteps.forEach((step, index) => {
            if (index <= currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
    }

    function validateStep(stepIndex) {
        const currentStepElement = steps[stepIndex];
        const visaRecord = document.getElementById('id_visa_apply_record');
        const visaDetails = document.getElementById('id_visa_details');
        if (visaRecord && visaDetails) {
            if (visaRecord.value === 'yes') {
                visaDetails.setAttribute('required', 'required');
                const label = document.getElementById('label_visa_details');
                if (label) label.classList.add('required');
            } else {
                visaDetails.removeAttribute('required');
                const label = document.getElementById('label_visa_details');
                if (label) label.classList.remove('required');
            }
        }

        const maritalStatus = document.getElementById('id_marital_status');
        const spouseFields = {
            'id_spouse_name': 'label_spouse_name',
            'id_spouse_contact': 'label_spouse_contact'
        };
        if (maritalStatus) {
            const isMarried = maritalStatus.value === 'married';
            Object.keys(spouseFields).forEach(fieldId => {
                const input = document.getElementById(fieldId);
                const label = document.getElementById(spouseFields[fieldId]);
                if (input) {
                    if (isMarried) {
                        input.setAttribute('required', 'required');
                        if (label) label.classList.add('required');
                    } else {
                        input.removeAttribute('required');
                        if (label) label.classList.remove('required');
                    }
                }
            });
        }

        const requiredFields = currentStepElement.querySelectorAll('[required]');
        let isValid = true;
        requiredFields.forEach(field => { validateField(field); });

        function validateField(field) {
            let fieldValid = true;
            const val = field.value.trim();
            const isVisaDetails = field.id === 'id_visa_details';
            const visaRecordVal = document.getElementById('id_visa_apply_record')?.value;
            const isActuallyRequired = field.hasAttribute('required') || (isVisaDetails && visaRecordVal === 'yes');

            if (isActuallyRequired && !val) {
                fieldValid = false;
            } else if (field.hasAttribute('pattern') && val) {
                const regex = new RegExp('^' + field.getAttribute('pattern') + '$');
                if (!regex.test(val)) {
                    fieldValid = false;
                }
            }

            let errorMsgOverride = null;
            if (field.id === 'id_date_of_birth' && val) {
                const dob = new Date(val);
                const today = new Date();
                let age = today.getFullYear() - dob.getFullYear();
                const monthDiff = today.getMonth() - dob.getMonth();
                if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
                    age--;
                }
                if (age < 18) {
                    fieldValid = false;
                    errorMsgOverride = "You must be at least 18 years old.";
                }
            }

            if (!fieldValid) {
                field.classList.add('error');
                isValid = false;
                let errorDiv = field.parentElement.querySelector('.field-error');
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'field-error';
                    field.parentElement.appendChild(errorDiv);
                }
                const errorMsg = errorMsgOverride || ((field.hasAttribute('pattern') && val)
                    ? field.getAttribute('title') || 'Invalid format'
                    : 'This field is required');
                errorDiv.innerHTML = `<span>⚠️</span> ${errorMsg}`;
            } else {
                field.classList.remove('error');
                const errorDiv = field.parentElement.querySelector('.field-error');
                if (errorDiv) { errorDiv.remove(); }
            }
            return fieldValid;
        }

        const allInputs = currentStepElement.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            if (!input.dataset.validationAttached) {
                input.addEventListener('blur', () => validateField(input));
                input.addEventListener('input', () => {
                    if (input.classList.contains('error')) {
                        validateField(input);
                    }
                });
                input.dataset.validationAttached = 'true';
            }
        });

        if (!isValid) {
            const firstError = currentStepElement.querySelector('.error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        return isValid;
    }

    // Photo upload with drag & drop
    const photoUploadArea = document.getElementById('photoUploadArea');
    const photoInput = document.getElementById('id_photo');
    const photoPreview = document.getElementById('photoPreview');

    if (photoUploadArea && photoInput) {
        photoUploadArea.addEventListener('click', () => photoInput.click());
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            photoUploadArea.addEventListener(eventName, preventDefaults, false);
        });
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        ['dragenter', 'dragover'].forEach(eventName => {
            photoUploadArea.addEventListener(eventName, highlight, false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            photoUploadArea.addEventListener(eventName, unhighlight, false);
        });
        function highlight() { photoUploadArea.classList.add('dragover'); }
        function unhighlight() { photoUploadArea.classList.remove('dragover'); }
        photoUploadArea.addEventListener('drop', handleDrop, false);
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
        photoInput.addEventListener('change', function () { handleFiles(this.files); });

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (!file.type.match('image.*')) {
                    alert('Please upload an image file (JPEG, PNG, GIF)');
                    return;
                }
                const reader = new FileReader();
                reader.onload = function (e) {
                    photoPreview.src = e.target.result;
                    photoUploadArea.classList.add('has-photo');
                };
                reader.readAsDataURL(file);
            }
        }
    }

    // Medical report file upload
    const medicalReportCard = document.querySelector('.document-card[data-doc="medical_report"]');
    if (medicalReportCard) {
        const medicalReportInput = medicalReportCard.querySelector('input[type="file"]');
        medicalReportCard.addEventListener('click', () => medicalReportInput.click());
        medicalReportInput.addEventListener('change', function () {
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileInfo = medicalReportCard.querySelector('.document-file-info');
                if (file.size > 10 * 1024 * 1024) {
                    alert(`"${file.name}" exceeds the 10MB limit.`);
                    this.value = '';
                    fileInfo.textContent = '';
                    medicalReportCard.classList.remove('has-file');
                    return;
                }
                fileInfo.textContent = `✓ ${file.name} (${formatFileSize(file.size)})`;
                medicalReportCard.classList.add('has-file');
            }
        });
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            medicalReportCard.addEventListener(eventName, preventDefaults, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            medicalReportCard.addEventListener(eventName, function () {
                medicalReportCard.classList.add('dragover');
            }, false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            medicalReportCard.addEventListener(eventName, function () {
                medicalReportCard.classList.remove('dragover');
            }, false);
        });
        medicalReportCard.addEventListener('drop', function (e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                medicalReportInput.files = files;
                medicalReportInput.dispatchEvent(new Event('change'));
            }
        }, false);
    }

    // Document upload functionality
    const documentCards = document.querySelectorAll('.document-card');
    documentCards.forEach(card => {
        const input = card.querySelector('input[type="file"]');
        card.addEventListener('click', () => input.click());
        input.addEventListener('change', function () {
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileInfo = card.querySelector('.document-file-info');
                const docType = card.getAttribute('data-doc');
                if (file.size > 10 * 1024 * 1024) {
                    alert(`"${file.name}" exceeds the 10MB limit.`);
                    this.value = '';
                    fileInfo.textContent = '';
                    card.classList.remove('has-file');
                    return;
                }
                fileInfo.textContent = `✓ ${file.name} (${formatFileSize(file.size)})`;
                card.classList.add('has-file');
                const checkBox = document.getElementById('check_documents');
                if (checkBox) { checkBox.checked = true; }
            }
        });
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            card.addEventListener(eventName, preventDefaults, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            card.addEventListener(eventName, function () {
                card.classList.add('dragover');
            }, false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            card.addEventListener(eventName, function () {
                card.classList.remove('dragover');
            }, false);
        });
        card.addEventListener('drop', function (e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                input.files = files;
                input.dispatchEvent(new Event('change'));
            }
        }, false);
    });

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Visa details toggle
    const visaRecordField = document.getElementById('id_visa_apply_record');
    const visaDetailsContainer = document.getElementById('visaDetailsContainer');
    if (visaRecordField && visaDetailsContainer) {
        visaRecordField.addEventListener('change', function () {
            visaDetailsContainer.style.display = this.value === 'yes' ? 'block' : 'none';
        });
    }

    // Spouse details toggle
    const maritalStatusField = document.getElementById('id_marital_status');
    const spouseNameContainer = document.getElementById('spouseNameContainer');
    const spouseContactContainer = document.getElementById('spouseContactContainer');
    function toggleSpouseFields() {
        if (maritalStatusField.value === 'married') {
            spouseNameContainer.style.display = 'block';
            spouseContactContainer.style.display = 'block';
        } else {
            spouseNameContainer.style.display = 'none';
            spouseContactContainer.style.display = 'none';
        }
    }
    if (maritalStatusField && spouseNameContainer && spouseContactContainer) {
        maritalStatusField.addEventListener('change', function () {
            toggleSpouseFields();
            if (typeof validateStep === 'function') { validateStep(currentStep); }
        });
        toggleSpouseFields();
    }

    // Review all information button
    const reviewAllBtn = document.getElementById('reviewAllBtn');
    if (reviewAllBtn) {
        reviewAllBtn.addEventListener('click', function () {
            currentStep = 0;
            updateStepDisplay();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Form submission
    const studentForm = document.getElementById('studentForm');
    if (studentForm) {
        studentForm.addEventListener('submit', function (e) {
            let allValid = true;
            for (let i = 0; i < steps.length - 1; i++) {
                if (!validateStep(i)) {
                    allValid = false;
                    currentStep = i;
                    updateStepDisplay();
                    break;
                }
            }
            if (!allValid) {
                e.preventDefault();
                alert('Please complete all required fields before submitting.');
                return false;
            }
            const activeSubmitBtn = this.querySelector('#submitBtn, #finalSubmitBtn');
            if (activeSubmitBtn) {
                activeSubmitBtn.classList.add('loading');
                activeSubmitBtn.disabled = true;
                activeSubmitBtn.innerHTML = '<span class="spinner"></span> Submitting...';
            }
            return true;
        });
    }

    // Auto-update checklist
    function updateChecklist() {
        const personalFields = ['full_name', 'date_of_birth', 'permanent_address', 'email', 'phone'];
        let personalComplete = true;
        personalFields.forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field && !field.value.trim()) { personalComplete = false; }
        });
        document.getElementById('check_personal').checked = personalComplete;

        const mandatorySchools = ['school_primary_school', 'school_junior_h_school', 'school_higher_s_school'];
        let educationComplete = true;
        mandatorySchools.forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (!field || !field.value.trim()) { educationComplete = false; }
        });
        document.getElementById('check_education').checked = educationComplete;

        const workFields = ['work_type_1', 'company_name_1'];
        let experienceComplete = false;
        workFields.forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field && field.value.trim()) { experienceComplete = true; }
        });
        document.getElementById('check_experience').checked = experienceComplete;

        const docInputs = document.querySelectorAll('.document-card input[type="file"]');
        let documentsComplete = false;
        docInputs.forEach(input => {
            if (input.files.length > 0) { documentsComplete = true; }
        });
        document.getElementById('check_documents').checked = documentsComplete;
    }

    document.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('change', updateChecklist);
        field.addEventListener('input', updateChecklist);
    });
    updateChecklist();

    // Phone input: strip non-numeric characters, max 10 digits
    const phoneInput = document.getElementById('id_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    }

    // Auto-calculate age from date of birth
    const dobInput = document.getElementById('id_date_of_birth');
    if (dobInput) {
        dobInput.addEventListener('change', function () {
            if (!this.value) {
                const ageInput = document.getElementById('id_age');
                if (ageInput) ageInput.value = '';
                return;
            }
            const dob = new Date(this.value);
            if (isNaN(dob.getTime())) return;
            const today = new Date();
            let age = today.getFullYear() - dob.getFullYear();
            const m = today.getMonth() - dob.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) { age--; }
            const ageInput = document.getElementById('id_age');
            if (ageInput) ageInput.value = age;
        });
    }

    // Passport expiry: minimum date is today
    const passportExpiry = document.getElementById('id_passport_expiry_date');
    if (passportExpiry) {
        const today = new Date().toISOString().split('T')[0];
        passportExpiry.setAttribute('min', today);
    }
});
