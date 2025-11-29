/**
 * Alpine.js component for Brazilian money input formatting
 * Uses Cleave.js for real-time formatting
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('moneyInput', (initialValue = '') => {
    return {
      cleaveInstance: null,
      
      init() {
        // Initialize Cleave.js for Brazilian Real formatting
        if (this.$refs.input) {
          this.cleaveInstance = new Cleave(this.$refs.input, {
            numeral: true,
            numeralDecimalMark: ',',
            numeralThousandsGroupStyle: 'thousand',
            numeralDecimalScale: 2,
            prefix: 'R$ ',
            rawValueTrimPrefix: true,
            onValueChanged: (e) => {
              // Update hidden field with raw value
              // Cleave.js with numeral:true returns rawValue as digits only (e.g., "120050" for R$ 1.200,50)
              // We need to convert to decimal format: divide by 100 to get the decimal value
              const rawValue = e.target.rawValue || '';
              let numericValue = '0.00';
              
              if (rawValue) {
                // Convert string of digits to decimal: last 2 digits are cents
                // Example: "120050" -> "1200.50"
                const digits = rawValue.replace(/\D/g, ''); // Remove any non-digit characters (safety)
                if (digits.length > 0) {
                  const integerPart = digits.slice(0, -2) || '0';
                  const decimalPart = digits.slice(-2).padStart(2, '0');
                  numericValue = `${integerPart}.${decimalPart}`;
                }
              }
              
              if (this.$refs.hiddenInput) {
                this.$refs.hiddenInput.value = numericValue;
              }
            }
          });
          
          // Set initial value if provided
          if (initialValue) {
            // Initial value comes from Django as decimal string (e.g., "1200.50")
            // Convert to Brazilian format for Cleave.js: "1200.50" -> "120050" (digits only)
            const decimalStr = String(initialValue).replace(/[^\d.]/g, '');
            if (decimalStr) {
              // Remove decimal point and pad to ensure 2 decimal places
              const parts = decimalStr.split('.');
              const integerPart = parts[0] || '0';
              const decimalPart = (parts[1] || '00').padEnd(2, '0').slice(0, 2);
              const digitsOnly = integerPart + decimalPart;
              this.cleaveInstance.setRawValue(digitsOnly);
              // Also update hidden input with original decimal format
              if (this.$refs.hiddenInput) {
                this.$refs.hiddenInput.value = decimalStr;
              }
            }
          }
        }
      }
    };
  });
});

