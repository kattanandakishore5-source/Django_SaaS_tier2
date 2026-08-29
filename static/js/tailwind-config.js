/* Tailwind config for CDN build */
window.tailwind = window.tailwind || {};

window.tailwindConfig = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: { DEFAULT: '#3b82f6', 50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' },
                accent:  { DEFAULT: '#8b5cf6', 400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed' },
            }
        }
    }
};

try {
    window.tailwind = window.tailwind || {};
    window.tailwind.config = window.tailwindConfig;
} catch (e) {
    // noop
}
