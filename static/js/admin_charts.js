/**
 * ADMIN COMMAND CENTER ANALYTICS - CHART.JS VISUALIZATIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  initAdminCharts();
});

function initAdminCharts() {
  // 1. Disaster Types Doughnut Chart
  const typeCanvas = document.getElementById('disasterTypeChart');
  if (typeCanvas && window.chartDataDisasterTypes) {
    const labels = Object.keys(window.chartDataDisasterTypes);
    const data = Object.values(window.chartDataDisasterTypes);

    new Chart(typeCanvas, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['Flood', 'Cyclone', 'Storm', 'Landslide'],
        datasets: [{
          data: data.length ? data : [4, 3, 2, 1],
          backgroundColor: ['#3b82f6', '#06b6d4', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8' } }
        }
      }
    });
  }

  // 2. Rescue Status Pie Chart
  const rescueCanvas = document.getElementById('rescueStatusChart');
  if (rescueCanvas && window.chartDataRescueStatus) {
    new Chart(rescueCanvas, {
      type: 'pie',
      data: {
        labels: ['Pending', 'Assigned', 'In Progress', 'Resolved'],
        datasets: [{
          data: [
            window.chartDataRescueStatus['Pending'] || 1,
            window.chartDataRescueStatus['Assigned'] || 2,
            window.chartDataRescueStatus['In Progress'] || 1,
            window.chartDataRescueStatus['Resolved'] || 4
          ],
          backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8' } }
        }
      }
    });
  }

  // 3. Monthly Incident Activity Bar Chart
  const monthlyCanvas = document.getElementById('monthlyIncidentsChart');
  if (monthlyCanvas) {
    new Chart(monthlyCanvas, {
      type: 'bar',
      data: {
        labels: ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [
          {
            label: 'Disaster Incidents',
            data: [2, 5, 8, 14, 11, 7, 4, 3],
            backgroundColor: 'rgba(239, 68, 68, 0.75)',
            borderRadius: 6
          },
          {
            label: 'Rescue Missions',
            data: [1, 4, 6, 12, 9, 5, 3, 2],
            backgroundColor: 'rgba(59, 130, 246, 0.75)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        },
        plugins: {
          legend: { labels: { color: '#cbd5e1' } }
        }
      }
    });
  }
}
