// Alpine.js + HTMX initialization
document.addEventListener('DOMContentLoaded', () => {
  // Redirect HTMX boost to Alpine  
  htmx.config.refreshOnHistoryMiss = true;
  htmx.config.timeout = 10000;
});

// Helpers for form handling
function handleHTMXResponse(detail) {
  const { xhr } = detail;
  if (xhr.status === 403) {
    alert('Accès refusé: vous n\'avez pas les permissions nécessaires.');
  } else if (xhr.status >= 500) {
    console.error('Server error:', xhr.responseText);
  }
}

document.addEventListener('htmx:responseError', handleHTMXResponse);

// Export for use in templates
window.htmxHelpers = {
  handleHTMXResponse
};
