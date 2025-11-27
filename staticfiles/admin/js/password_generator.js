(function($) {
    'use strict';
    
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
    
    $(document).ready(function() {
        // Find the password field in add form
        const passwordField = $('input[name="password"]');
        
        if (passwordField.length) {
            // Create generate button
            const generateButton = $('<button type="button" class="generate-password-btn" style="margin-left: 10px; padding: 5px 10px; background: #417690; color: white; border: none; border-radius: 3px; cursor: pointer;">Generate Password</button>');
            
            // Create clear button
            const clearButton = $('<button type="button" class="clear-password-btn" style="margin-left: 5px; padding: 5px 10px; background: #ba2121; color: white; border: none; border-radius: 3px; cursor: pointer;">Clear</button>');
            
            // Insert buttons after password field
            passwordField.after(generateButton);
            passwordField.after(clearButton);
            
            // Generate password button click
            generateButton.click(function() {
                const newPassword = generatePassword(12);
                passwordField.val(newPassword);
                
                // Show success message
                const message = $('<div class="password-message" style="color: green; margin-top: 5px; font-size: 12px;">Password generated! User can still change it via activation email.</div>');
                $('.password-message').remove(); // Remove existing messages
                passwordField.after(message);
            });
            
            // Clear password button click
            clearButton.click(function() {
                passwordField.val('');
                $('.password-message').remove();
                
                // Show info message
                const message = $('<div class="password-message" style="color: blue; margin-top: 5px; font-size: 12px;">Password cleared. User will set password via activation email.</div>');
                $('.password-message').remove(); // Remove existing messages
                passwordField.after(message);
            });
            
            // Add some styling to the password field
            passwordField.css('width', '300px');
        }
    });
    
})(django.jQuery);