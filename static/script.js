// Initialize map and store globally
let map;
let currentMarkers = [];
let currentConnections = [];

async function initializeMap() {
    try {
        const response = await fetch('/api/config/map');
        const config = await response.json();
        
        if (!config.accessToken) {
            throw new Error('No Mapbox access token found');
        }
        
        mapboxgl.accessToken = config.accessToken;
        map = new mapboxgl.Map({
            container: 'map',
            style: 'mapbox://styles/mapbox/light-v11',
            center: config.center,
            zoom: config.zoom
        });

        // Wait for map to load
        await new Promise((resolve, reject) => {
            map.on('load', resolve);
            map.on('error', reject);
        });

        console.log('Map initialized successfully');
    } catch (error) {
        console.error('Failed to initialize map:', error);
        $('#map').html('<div class="error-message">Failed to load map. Please check your Mapbox access token.</div>');
    }
}

function clearMap() {
    // Remove existing markers
    currentMarkers.forEach(marker => marker.remove());
    currentMarkers = [];

    // Remove existing connections
    currentConnections.forEach(connectionId => {
        if (map.getLayer(connectionId)) {
            map.removeLayer(connectionId);
        }
        if (map.getSource(connectionId)) {
            map.removeSource(connectionId);
        }
    });
    currentConnections = [];
}

function addCompanyToMap(company, isCenter = false) {
    if (!company.latitude || !company.longitude) return null;

    const el = document.createElement('div');
    el.className = 'marker';
    el.style.width = '20px';
    el.style.height = '20px';
    el.style.borderRadius = '50%';
    el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
    el.style.border = '3px solid white';
    el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    el.style.cursor = 'pointer';

    // Create popup
    const popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 25,
        className: 'custom-popup'
    })
    .setHTML(`
        <div class="popup-content">
            <h4>${company.name}</h4>
            ${company.domain ? `<a href="https://${company.domain}" target="_blank" class="popup-domain">${company.domain}</a>` : ''}
        </div>
    `);

    // Create marker
    const marker = new mapboxgl.Marker({
        element: el,
        anchor: 'center'
    })
    .setLngLat([company.longitude, company.latitude])
    .setPopup(popup)
    .addTo(map);

    // Show popup on hover
    el.addEventListener('mouseenter', () => {
        marker.getPopup().addTo(map);
        el.style.backgroundColor = isCenter ? '#1d4ed8' : '#475569';
    });
    
    el.addEventListener('mouseleave', () => {
        marker.getPopup().remove();
        el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
    });

    currentMarkers.push(marker);
    return marker;
}

function drawConnection(source, target, index) {
    if (!source || !target || !source.longitude || !source.latitude || !target.longitude || !target.latitude) return;

    const connectionId = `connection-${index}`;
    currentConnections.push(connectionId);

    // Calculate midpoint
    const midLon = (source.longitude + target.longitude) / 2;
    const midLat = (source.latitude + target.latitude) / 2;

    // Calculate distance for curve height
    const dx = target.longitude - source.longitude;
    const dy = target.latitude - source.latitude;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // Add curve by creating a control point above the midpoint
    const curveHeight = distance * 0.2;
    const controlPoint = [midLon, midLat + curveHeight];

    // Generate curved path using quadratic Bezier
    const curvePoints = [];
    const steps = 50;
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const point = [
            (1 - t) * (1 - t) * source.longitude + 2 * (1 - t) * t * controlPoint[0] + t * t * target.longitude,
            (1 - t) * (1 - t) * source.latitude + 2 * (1 - t) * t * controlPoint[1] + t * t * target.latitude
        ];
        curvePoints.push(point);
    }

    // Add the curve layer
    map.addLayer({
        'id': connectionId,
        'type': 'line',
        'source': {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': curvePoints
                }
            }
        },
        'layout': {
            'line-join': 'round',
            'line-cap': 'round'
        },
        'paint': {
            'line-color': '#2563eb',
            'line-width': 2,
            'line-opacity': 0.6
        }
    });
}

function updateMapView(companies) {
    if (!companies || companies.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();
    companies.forEach(company => {
        if (company.latitude && company.longitude) {
            bounds.extend([company.longitude, company.latitude]);
        }
    });

    map.fitBounds(bounds, {
        padding: 50,
        maxZoom: 15
    });
}

function displayCompanies(data, containerId, type) {
    const resultsContainer = $(containerId).empty();
    
    if (!data || !data.center || !data.related || data.related.length === 0) {
        resultsContainer.append(`<p>No ${type.toLowerCase()} found.</p>`);
        clearMap();
        return;
    }

    // Clear previous markers and connections
    clearMap();

    const centerCompany = data.center;
    const companies = data.related;

    // Display header with count
    const count = companies.length;
    let headerText;
    if (type === 'Clients') {
        headerText = count === 1
            ? `Company ${centerCompany.name} provides deals to the following 1 client:`
            : count === 0
            ? `Company ${centerCompany.name} provides no deals to clients at the moment`
            : `Company ${centerCompany.name} provides deals to the following ${count} clients:`;
    } else {
        headerText = count === 1
            ? `Client ${centerCompany.name} receives deals from the following 1 company:`
            : count === 0
            ? `Client ${centerCompany.name} receives no deals from companies at the moment`
            : `Client ${centerCompany.name} receives deals from the following ${count} companies:`;
    }
    resultsContainer.append(`<h3>${headerText}</h3>`);

    // Create cards for each company
    companies.forEach(company => {
        const card = $('<div>').addClass('company-card');
        const nameEl = $('<h4>').text(company.name);
        card.append(nameEl);

        if (company.domain) {
            const domainLink = $('<a>')
                .addClass('company-domain')
                .attr('href', `https://${company.domain}`)
                .attr('target', '_blank')
                .text(company.domain);
            card.append(domainLink);
        }

        resultsContainer.append(card);
    });

    // Update map
    clearMap();
    const centerMarker = addCompanyToMap(centerCompany, true);

    // Add company markers and connections
    companies.forEach((company, index) => {
        const marker = addCompanyToMap(company);
        if (marker && centerMarker) {
            drawConnection(centerCompany, company, index);
        }
    });

    // Update map view
    updateMapView([centerCompany, ...companies]);
}

function displayError(containerId, message) {
    $(containerId).empty().append(
        `<div class="error-message">${message}</div>`
    );
}

// Initialize when document is ready
$(document).ready(async function() {
    // Initialize the map
    await initializeMap();

    // Initialize Select2 for vendor search
    $('#vendor-search').select2({
        placeholder: 'Search for a vendor...',
        allowClear: true,
        ajax: {
            url: '/api/search/vendors',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term || ''
                };
            },
            processResults: function(data) {
                return {
                    results: data.results.map(function(item) {
                        return {
                            id: item.name,
                            text: item.name
                        };
                    })
                };
            },
            cache: true
        },
        minimumInputLength: 1
    });

    // Initialize Select2 for client search
    $('#client-search').select2({
        placeholder: 'Search for a client...',
        allowClear: true,
        ajax: {
            url: '/api/search/clients',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term || ''
                };
            },
            processResults: function(data) {
                return {
                    results: data.results.map(function(item) {
                        return {
                            id: item.name,
                            text: item.name
                        };
                    })
                };
            },
            cache: true
        },
        minimumInputLength: 1
    });

    // Handle vendor selection
    $('#vendor-search').on('select2:select', function(e) {
        const vendorName = e.params.data.id;
        $.get(`/api/relationships/vendor/${encodeURIComponent(vendorName)}`)
            .done(function(data) {
                if (data && data.center) {
                    displayCompanies(data, '#vendor-results', 'Clients');
                } else {
                    displayError('#vendor-results', 'No relationships found for this vendor');
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Failed to fetch clients:', errorThrown);
                displayError('#vendor-results', 'Failed to fetch clients');
            });
    });

    // Handle client selection
    $('#client-search').on('select2:select', function(e) {
        const clientName = e.params.data.id;
        $.get(`/api/relationships/client/${encodeURIComponent(clientName)}`)
            .done(function(data) {
                if (data && data.center) {
                    displayCompanies(data, '#client-results', 'Vendors');
                } else {
                    displayError('#client-results', 'No relationships found for this client');
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Failed to fetch vendors:', errorThrown);
                displayError('#client-results', 'Failed to fetch vendors');
            });
    });

    // Handle clear
    $('#vendor-search, #client-search').on('select2:clear', function() {
        const resultId = $(this).attr('id') === 'vendor-search' ? '#vendor-results' : '#client-results';
        $(resultId).empty();
        clearMap();
    });
});
