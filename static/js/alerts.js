/**
 * DISASTER ALERTS CLIENT-SIDE FILTER
 */

document.addEventListener('DOMContentLoaded', function () {
  const filterForm = document.getElementById('alertFilterForm');
  const alertCards = document.querySelectorAll('.disaster-alert-card');

  if (filterForm) {
    const inputs = filterForm.querySelectorAll('select, input');
    inputs.forEach(input => {
      input.addEventListener('change', filterAlerts);
      if (input.type === 'text') {
        input.addEventListener('input', filterAlerts);
      }
    });
  }

  function filterAlerts() {
    const category = document.getElementById('filterCategory')?.value.toLowerCase() || 'all';
    const severity = document.getElementById('filterSeverity')?.value.toLowerCase() || 'all';
    const search = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';

    let visibleCount = 0;

    alertCards.forEach(card => {
      const cardCategory = (card.getAttribute('data-category') || '').toLowerCase();
      const cardSeverity = (card.getAttribute('data-severity') || '').toLowerCase();
      const cardText = card.innerText.toLowerCase();

      const matchesCat = (category === 'all' || cardCategory === category);
      const matchesSev = (severity === 'all' || cardSeverity === severity);
      const matchesSearch = (!search || cardText.includes(search));

      if (matchesCat && matchesSev && matchesSearch) {
        card.style.display = 'block';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    const countLabel = document.getElementById('filteredAlertsCount');
    if (countLabel) {
      countLabel.textContent = `${visibleCount} Alert(s) Found`;
    }
  }
});
