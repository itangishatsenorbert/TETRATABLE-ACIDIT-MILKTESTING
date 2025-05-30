// Configuration
const config = {
    updateInterval: 2000, // 2 seconds
    apiEndpoints: {
        realtime: '/api/realtime',
        historical: '/api/data',
        systemStatus: '/api/system/status'
    }
};

// Chart instances
const charts = {
    ta: null,
    temp: null,
    ph: null,
    cond: null,
    combined: null
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initializeCharts();

    // Start data updates
    startDataUpdates();

    // Check system status periodically
    setInterval(checkSystemStatus, 5000);
});

function initializeCharts() {
    const chartConfig = {
        type: 'line',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                },
                y: {
                    beginAtZero: false
                }
            },
            animation: {
                duration: 0
            }
        }
    };

    charts.ta = new Chart(document.getElementById('taChart'), {
        ...chartConfig,
        data: {
            datasets: [{
                label: 'Titratable Acidity',
                borderColor: 'rgb(13, 110, 253)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.1
            }]
        }
    });

    charts.temp = new Chart(document.getElementById('tempChart'), {
        ...chartConfig,
        data: {
            datasets: [{
                label: 'Temperature (°C)',
                borderColor: 'rgb(220, 53, 69)',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.1
            }]
        }
    });

    charts.ph = new Chart(document.getElementById('phChart'), {
        ...chartConfig,
        data: {
            datasets: [{
                label: 'pH Level',
                borderColor: 'rgb(25, 135, 84)',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                tension: 0.1
            }]
        }
    });

    charts.cond = new Chart(document.getElementById('condChart'), {
        ...chartConfig,
        data: {
            datasets: [{
                label: 'Conductivity (µS/cm)',
                borderColor: 'rgb(255, 193, 7)',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.1
            }]
        }
    });

    charts.combined = new Chart(document.getElementById('combinedChart'), {
        ...chartConfig,
        options: {
            ...chartConfig.options,
            scales: {
                ...chartConfig.options.scales,
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        },
        data: {
            datasets: [
                {
                    label: 'TA',
                    yAxisID: 'y',
                    borderColor: 'rgb(13, 110, 253)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.1
                },
                {
                    label: 'Temp (°C)',
                    yAxisID: 'y1',
                    borderColor: 'rgb(220, 53, 69)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.1
                },
                {
                    label: 'pH',
                    yAxisID: 'y',
                    borderColor: 'rgb(25, 135, 84)',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.1
                },
                {
                    label: 'Cond (µS/cm)',
                    yAxisID: 'y1',
                    borderColor: 'rgb(255, 193, 7)',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.1
                }
            ]
        }
    });
}

function startDataUpdates() {
    updateData();
    setInterval(updateData, config.updateInterval);
}

function updateData() {
    document.getElementById('loadingIndicator').style.display = 'flex';

    fetch(config.apiEndpoints.realtime)
        .then(response => response.json())
        .then(data => {
            document.getElementById('lastUpdateTime').textContent =
                new Date(data.timestamp).toLocaleTimeString();

            if (data.ta.length > 0) {
                document.getElementById('taValue').textContent = data.ta[data.ta.length - 1].toFixed(3);
                document.getElementById('tempValue').textContent = data.temp[data.temp.length - 1].toFixed(1);
                document.getElementById('phValue').textContent = data.ph[data.ph.length - 1].toFixed(2);
                document.getElementById('condValue').textContent = data.cond[data.cond.length - 1].toFixed(2);
                document.getElementById('dataStatus').textContent = `Status: ${data.status[data.status.length - 1]}`;
            }

            updateChartData(charts.ta, data.time, data.ta);
            updateChartData(charts.temp, data.time, data.temp);
            updateChartData(charts.ph, data.time, data.ph);
            updateChartData(charts.cond, data.time, data.cond);

            updateCombinedChart(data);
            updateDataTable(data);
            document.getElementById('loadingIndicator').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching real-time data:', error);
            document.getElementById('connectionAlert').className = 'alert alert-danger alert-dismissible fade show mb-0';
            document.getElementById('connectionStatus').textContent = 'Connection Error';
            document.getElementById('connectionDetails').textContent = error.message;
            document.getElementById('loadingIndicator').style.display = 'none';
        });

    fetch(config.apiEndpoints.historical)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error in historical data:', data.error);
                return;
            }
            document.getElementById('dataCount').textContent = `${data.data.length} records`;
        })
        .catch(error => {
            console.error('Error fetching historical data:', error);
        });
}

function updateChartData(chart, labels, data) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data.map((value, index) => ({
        x: labels[index],
        y: value
    }));
    chart.update();
}

function updateCombinedChart(data) {
    const chart = charts.combined;
    chart.data.labels = data.time;
    chart.data.datasets[0].data = data.ta.map((value, index) => ({ x: data.time[index], y: value }));
    chart.data.datasets[1].data = data.temp.map((value, index) => ({ x: data.time[index], y: value }));
    chart.data.datasets[2].data = data.ph.map((value, index) => ({ x: data.time[index], y: value }));
    chart.data.datasets[3].data = data.cond.map((value, index) => ({ x: data.time[index], y: value }));
    chart.update();
}

function updateDataTable(data) {
    const tbody = document.querySelector('#readingsTable tbody');
    tbody.innerHTML = '';

    if (data.time.length === 0) return;

    const count = Math.min(5, data.time.length);

    for (let i = 0; i < count; i++) {
        const idx = data.time.length - 1 - i;
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${data.time[idx]}</td>
            <td>${data.ta[idx].toFixed(3)}</td>
            <td>${data.temp[idx].toFixed(1)}</td>
            <td>${data.ph[idx].toFixed(2)}</td>
            <td>${data.cond[idx].toFixed(2)}</td>
            <td><span class="badge ${getStatusBadgeClass(data.status[idx])}">${data.status[idx]}</span></td>
        `;

        tbody.appendChild(row);
    }
}

function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'normal': return 'bg-success';
        case 'warning': return 'bg-warning text-dark';
        case 'alert': return 'bg-danger';
        case 'simulated': return 'bg-info text-dark';
        default: return 'bg-secondary';
    }
}

function checkSystemStatus() {
    fetch(config.apiEndpoints.systemStatus)
        .then(response => response.json())
        .then(data => {
            let statusText = 'System Status: ';
            let alertClass = '';

            if (data.database_connected && !data.serial_connected) {
                statusText += 'Running (Database Only)';
                alertClass = 'alert-warning';
            } else if (data.database_connected && data.serial_connected) {
                statusText += 'Running (Full System)';
                alertClass = 'alert-success';
            } else {
                statusText += 'Degraded';
                alertClass = 'alert-danger';
            }

            document.getElementById('systemStatus').textContent = statusText;
            document.getElementById('connectionAlert').className = `alert ${alertClass} alert-dismissible fade show mb-0`;
            document.getElementById('connectionStatus').textContent = statusText;

            const details = [];
            if (data.last_update) details.push(`Last update: ${data.last_update}`);
            details.push(`Buffer sizes: ${JSON.stringify(data.buffer_sizes)}`);

            document.getElementById('connectionDetails').textContent = details.join(' | ');
        })
        .catch(error => {
            console.error('Error checking system status:', error);
            document.getElementById('systemStatus').textContent = 'System Status: Error';
            document.getElementById('connectionAlert').className = 'alert alert-danger alert-dismissible fade show mb-0';
            document.getElementById('connectionStatus').textContent = 'Connection Error';
            document.getElementById('connectionDetails').textContent = error.message;
        });
}
