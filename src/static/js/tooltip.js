
document.addEventListener('DOMContentLoaded', () => {
// Target all elements with your custom class
const items = document.querySelectorAll('.dynamic-tooltip');

items.forEach(el => {
    // 1. Listen for when the user hovers over the element
    el.addEventListener('mouseenter', () => {
    
    // 2. Check if the text is actually overflowing/truncated
    if (el.scrollWidth > el.offsetWidth) {
        
        // 3. Set the tooltip text to the full text of the element
        el.setAttribute('data-bs-title', el.textContent.trim());
        
        // 4. Initialize and immediately show the Bootstrap tooltip
        const tooltip = bootstrap.Tooltip.getOrCreateInstance(el);
        tooltip.show();
    }
    });

    // 5. Clean up the tooltip when the mouse leaves
    el.addEventListener('mouseleave', () => {
    const tooltip = bootstrap.Tooltip.getInstance(el);
    if (tooltip) {
        tooltip.dispose(); // Removes the tooltip completely from memory
        el.removeAttribute('data-bs-title');
    }
    });
});
});
