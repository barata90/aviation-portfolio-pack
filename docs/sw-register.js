(function(){
function siteRoot(){ const p=location.pathname.split('/').filter(Boolean); return p.length?'/'+p[0]+'/':'/'; }
if ('serviceWorker' in navigator){
window.addEventListener('load', function(){
navigator.serviceWorker.register(siteRoot() + 'sw.js', {scope: siteRoot()})
.catch(err => console.warn('SW register fail:', err));
});
}
})();
