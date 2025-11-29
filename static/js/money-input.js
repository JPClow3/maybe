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
              // Update hidden field with raw value (comma to dot)
              const rawValue = e.target.rawValue || '';
              const numericValue = rawValue.replace(',', '.');
              if (this.$refs.hiddenInput) {
                this.$refs.hiddenInput.value = numericValue;
              }
            }
          });
          
          // Set initial value if provided
          if (initialValue) {
            const numericValue = String(initialValue).replace(/[^\d,.]/g, '').replace('.', ',');
            if (numericValue) {
              this.cleaveInstance.setRawValue(numericValue);
              // Also update hidden input
              if (this.$refs.hiddenInput) {
                this.$refs.hiddenInput.value = String(initialValue).replace(',', '.');
              }
            }
          }
        }
      }
    };
  });
});

