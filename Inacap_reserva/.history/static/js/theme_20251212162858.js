// theme.js - inyecta CSS dark si es necesario y provee toggle
(function(){
    const CSS_PATH = '/static/css/dark.css';
    const STORAGE_KEY = 'site_dark_mode';

    function isDark() {
        return localStorage.getItem(STORAGE_KEY) === '1';
    }

    function applyDark(dark){
        if(dark){
            document.body.classList.add('dark');
            // ensure stylesheet present
            if(!document.querySelector('link[data-theme="dark"]')){
                const l = document.createElement('link');
                l.rel = 'stylesheet';
                l.href = CSS_PATH;
                l.setAttribute('data-theme','dark');
                document.head.appendChild(l);
            }
        } else {
            document.body.classList.remove('dark');
            const l = document.querySelector('link[data-theme="dark"]');
            if(l) l.remove();
        }
    }

    window.toggleDarkMode = function(){
        const newVal = !isDark();
        localStorage.setItem(STORAGE_KEY, newVal ? '1' : '0');
        applyDark(newVal);
        // update any UI toggles
        document.querySelectorAll('[data-theme-toggle]').forEach(el=>{
            el.textContent = newVal ? '🌙' : '☀️';
        });
    };

    // apply on load
    document.addEventListener('DOMContentLoaded', function(){
        try{
            applyDark(isDark());
            // update toggles if present
            document.querySelectorAll('[data-theme-toggle]').forEach(el=>{
                el.textContent = isDark() ? '🌙' : '☀️';
                el.addEventListener('click', function(e){ e.preventDefault(); window.toggleDarkMode(); });
            });
        }catch(e){ console.warn('theme.js failed', e); }
    });
})();
