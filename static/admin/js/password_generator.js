// Wait for both jQuery and DOM to be ready
if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
    // jQuery is already available via Django
    (function($) {
        'use strict';
        
        console.log('Password generator script loaded with Django jQuery!');
        
        function generatePassword(length=12) {
            const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
            const lowercase = 'abcdefghijklmnopqrstuvwxyz';
            const numbers = '0123456789';
            const symbols = '!@#$%^&*';
            const allChars = uppercase + lowercase + numbers + symbols;
            
            let password = '';
            
            // Ensure at least one of each type
            password += uppercase[Math.floor(Math.random() * uppercase.length)];
            password += lowercase[Math.floor(Math.random() * lowercase.length)];
            password += numbers[Math.floor(Math.random() * numbers.length)];
            password += symbols[Math.floor(Math.random() * symbols.length)];
            
            // Fill the rest with random characters
            for (let i = password.length; i < length; i++) {
                password += allChars[Math.floor(Math.random() * allChars.length)];
            }
            
            // Shuffle the password
            return password.split('').sort(function() {
                return 0.5 - Math.random();
            }).join('');
        }
        
        function initPasswordGenerator() {
            console.log('Initializing password generator...');
            
            // Find the password field in add form - wait a bit for form to render
            setTimeout(function() {
                const passwordField = $('input[name="password"]');
                console.log('Found password fields:', passwordField.length);
                
                if (passwordField.length && !passwordField.closest('.form-row').find('.password-buttons-container').length) {
                    console.log('Creating buttons...');
                    
                    // Wrap the password field and add eye toggle button
                    const passwordWrapper = $('<div class="password-toggle-wrapper"></div>');
                    passwordField.wrap(passwordWrapper);
                    
                    // Create eye toggle button
                    const toggleButton = $('<button type="button" class="password-toggle-btn" title="Show password"></button>');
                    
                    // Insert toggle button after the password field (inside the wrapper)
                    passwordField.after(toggleButton);
                    
                    let isPasswordVisible = false;
                    
                    // Toggle password visibility
                    toggleButton.on('click', function() {
                        isPasswordVisible = !isPasswordVisible;
                        
                        if (isPasswordVisible) {
                            passwordField.attr('type', 'text');
                            toggleButton.addClass('show-password');
                            toggleButton.attr('title', 'Hide password');
                        } else {
                            passwordField.attr('type', 'password');
                            toggleButton.removeClass('show-password');
                            toggleButton.attr('title', 'Show password');
                        }
                    });
                    
                    // Create button container
                    const buttonContainer = $('<div class="password-buttons-container"></div>');
                    
                    // Create generate button - clean Django style
                    const generateButton = $('<button type="button" class="generate-password-btn">Generate password</button>');
                    
                    // Create clear button - clean Django style
                    const clearButton = $('<button type="button" class="clear-password-btn">Clear password</button>');
                    
                    // Add buttons to container
                    buttonContainer.append(generateButton);
                    buttonContainer.append(clearButton);
                    
                    // Insert container AFTER the help text (below the input)
                    const helpText = passwordField.closest('.form-row').find('.help');
                    if (helpText.length) {
                        // Insert after help text
                        helpText.after(buttonContainer);
                    } else {
                        // If no help text, insert after the input wrapper
                        passwordField.closest('.password-toggle-wrapper').after(buttonContainer);
                    }
                    
                    console.log('Buttons created and inserted below input');
                    
                    // Generate password button click
                    generateButton.on('click', function() {
                        console.log('Generate button clicked');
                        const newPassword = generatePassword(12);
                        passwordField.val(newPassword);
                        
                        // Show success message
                        $('.password-message').remove();
                        const message = $('<div class="password-message success">Password generated. It will be sent to the user.</div>');
                        buttonContainer.after(message);
                    });
                    
                    // Clear password button click
                    clearButton.on('click', function() {
                        console.log('Clear button clicked');
                        passwordField.val('');
                        $('.password-message').remove();
                        
                        // Show info message
                        const message = $('<div class="password-message info">Password cleared. Please generate or enter a password.</div>');
                        buttonContainer.after(message);
                    });
                    
                    console.log('Event listeners attached');
                } else {
                    console.log('Password field not found or buttons already exist');
                }
            }, 100);
        }
        
        // Initialize when document is ready
        $(document).ready(initPasswordGenerator);
        
        // Also try initializing after a delay in case the form loads dynamically
        setTimeout(initPasswordGenerator, 500);
        
    })(django.jQuery);
} else {
    console.log('Django jQuery not found, waiting for it to load...');
    
    // Fallback: wait for jQuery to load
    function waitForJQuery() {
        if (typeof window.jQuery !== 'undefined') {
            console.log('jQuery loaded, initializing password generator...');
            (function($) {
                'use strict';
                
                $(document).ready(function() {
                    setTimeout(function() {
                        const passwordField = $('input[name="password"]');
                        if (passwordField.length && !passwordField.closest('.form-row').find('.password-buttons-container').length) {
                            // Wrap and add eye toggle
                            const passwordWrapper = $('<div class="password-toggle-wrapper"></div>');
                            passwordField.wrap(passwordWrapper);
                            
                            const toggleButton = $('<button type="button" class="password-toggle-btn" title="Show password"></button>');
                            passwordField.after(toggleButton);
                            
                            let isPasswordVisible = false;
                            
                            toggleButton.on('click', function() {
                                isPasswordVisible = !isPasswordVisible;
                                if (isPasswordVisible) {
                                    passwordField.attr('type', 'text');
                                    toggleButton.addClass('show-password').attr('title', 'Hide password');
                                } else {
                                    passwordField.attr('type', 'password');
                                    toggleButton.removeClass('show-password').attr('title', 'Show password');
                                }
                            });
                            
                            const buttonContainer = $('<div class="password-buttons-container"></div>');
                            const generateButton = $('<button type="button" class="generate-password-btn">Generate password</button>');
                            const clearButton = $('<button type="button" class="clear-password-btn">Clear password</button>');
                            
                            buttonContainer.append(generateButton, clearButton);
                            
                            // Insert below the input (after help text)
                            const helpText = passwordField.closest('.form-row').find('.help');
                            if (helpText.length) {
                                helpText.after(buttonContainer);
                            } else {
                                passwordField.closest('.password-toggle-wrapper').after(buttonContainer);
                            }
                            
                            generateButton.on('click', function() {
                                const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
                                const lowercase = 'abcdefghijklmnopqrstuvwxyz';
                                const numbers = '0123456789';
                                const symbols = '!@#$%^&*';
                                const allChars = uppercase + lowercase + numbers + symbols;
                                
                                let password = '';
                                password += uppercase[Math.floor(Math.random() * uppercase.length)];
                                password += lowercase[Math.floor(Math.random() * lowercase.length)];
                                password += numbers[Math.floor(Math.random() * numbers.length)];
                                password += symbols[Math.floor(Math.random() * symbols.length)];
                                
                                for (let i = password.length; i < 12; i++) {
                                    password += allChars[Math.floor(Math.random() * allChars.length)];
                                }
                                
                                passwordField.val(password.split('').sort(() => 0.5 - Math.random()).join(''));
                                $('.password-message').remove();
                                buttonContainer.after('<div class="password-message success">Password generated. It will be sent to the user.</div>');
                            });
                            
                            clearButton.on('click', function() {
                                passwordField.val('');
                                $('.password-message').remove();
                                buttonContainer.after('<div class="password-message info">Password cleared. Please generate or enter a password.</div>');
                            });
                        }
                    }, 300);
                });
            })(window.jQuery);
        } else {
            setTimeout(waitForJQuery, 100);
        }
    }
    waitForJQuery();
}