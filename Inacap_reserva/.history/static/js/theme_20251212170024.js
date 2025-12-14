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
            // prefer existing link#darkCss if present
            let existing = document.getElementById('darkCss');
            if(existing){
                existing.disabled = false;
                existing.setAttribute('data-theme','dark');
            } else if(!document.querySelector('link[data-theme="dark"]')){
                const l = document.createElement('link');
                l.rel = 'stylesheet';
                l.href = CSS_PATH;
                l.id = 'darkCss';
                l.setAttribute('data-theme','dark');
                document.head.appendChild(l);
            }
        } else {
            document.body.classList.remove('dark');
            const existing = document.getElementById('darkCss');
            if(existing){ existing.disabled = true; existing.removeAttribute('data-theme'); }
            const l = document.querySelector('link[data-theme="dark"]');
            if(l) l.remove();
        }
    }

    window.toggleDarkMode = function(){
        const newVal = !isDark();
        localStorage.setItem(STORAGE_KEY, newVal ? '1' : '0');
        applyDark(newVal);
        // update any UI toggles (by attribute or class)
        document.querySelectorAll('[data-theme-toggle], .theme-toggle').forEach(el=>{
            try{ el.textContent = newVal ? '🌙' : '☀️'; }catch(e){}
        });
        // update debug marker
        try{ setThemeDebug(`theme.js: modo ${newVal? 'dark':'light'} · ${new Date().toLocaleTimeString()}`); }catch(e){}
    };

    // debug marker helper
    const DEBUG_ID = 'themeDebug';
    function setThemeDebug(text){
        let el = document.getElementById(DEBUG_ID);
        if(!el){
            el = document.createElement('div');
            el.id = DEBUG_ID;
            el.style.position = 'fixed';
            el.style.left = '8px';
            el.style.bottom = '8px';
            el.style.zIndex = 100000;
            el.style.background = 'rgba(0,0,0,0.6)';
            el.style.color = 'white';
            el.style.padding = '6px 8px';
            el.style.borderRadius = '6px';
            el.style.fontSize = '12px';
            el.style.fontFamily = 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif';
            el.style.pointerEvents = 'none';
            document.body.appendChild(el);
        }
        el.textContent = text;
    }

    // initializer used both for DOMContentLoaded and immediate execution
    function init(){
        try{
            applyDark(isDark());
            // update toggles if present
            const toggles = document.querySelectorAll('[data-theme-toggle], .theme-toggle');
            if(toggles.length){
                toggles.forEach(el=>{
                    el.textContent = isDark() ? '🌙' : '☀️';
                    el.addEventListener('click', function(e){ e.preventDefault(); window.toggleDarkMode(); });
                });
            } else {
                // inject a floating toggle so every page has it
                const btn = document.createElement('button');
                btn.setAttribute('data-theme-toggle','');
                btn.id = 'themeToggleInjected';
                btn.className = 'theme-toggle';
                btn.style.position = 'fixed';
                btn.style.right = '18px';
                btn.style.bottom = '18px';
                btn.style.zIndex = 99999;
                btn.style.width = '48px';
                btn.style.height = '48px';
                btn.style.borderRadius = '50%';
                btn.style.display = 'inline-flex';
                btn.style.alignItems = 'center';
                btn.style.justifyContent = 'center';
                btn.style.boxShadow = '0 8px 30px rgba(0,0,0,0.12)';
                btn.style.border = 'none';
                btn.style.cursor = 'pointer';
                btn.style.background = isDark() ? '#0b1220' : '#eef2ff';
                btn.style.color = isDark() ? '#e6eef8' : '#1f2937';
                btn.textContent = isDark() ? '🌙' : '☀️';
                btn.title = 'Cambiar tema';
                btn.addEventListener('click', function(e){ e.preventDefault(); window.toggleDarkMode(); });
                document.body.appendChild(btn);
            }
            // set debug marker after init
            try{ setThemeDebug(`theme.js: iniciado · modo ${isDark()? 'dark':'light'}`); }catch(e){}
        }catch(e){ console.warn('theme.js failed', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already ready (script loaded late) -> run immediately
        init();
    }
})();
