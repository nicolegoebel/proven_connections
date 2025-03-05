// Webflow-compatible script

// Initialize map and store globally
let map;
let currentMarkers = [];
let currentConnections = [];

function initializeMap() {
    // Fetch Mapbox configuration from API
    const response = await fetch('/api/config/map');
    const config = await response.json();
    mapboxgl.accessToken = config.accessToken;
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/light-v10',
        center: [-98.5795, 39.8283], // Center of USA
        zoom: 3
    });
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
    el.style.width = '15px';
    el.style.height = '15px';
    el.style.borderRadius = '50%';
    el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
    el.style.border = '2px solid white';
    el.style.boxShadow = '0 0 0 1px rgba(0,0,0,0.1)';

    const marker = new mapboxgl.Marker(el)
        .setLngLat([company.longitude, company.latitude])
        .setPopup(
            new mapboxgl.Popup({ offset: 25 })
                .setHTML(
                    `<h3>${company.name}</h3>
                     <p>${company.domain || ''}</p>`
                )
        )
        .addTo(map);

    currentMarkers.push(marker);
    return marker;
}

function drawConnection(source, target, index) {
    if (!source || !target) return;

    const connectionId = `connection-${index}`;
    currentConnections.push(connectionId);

    // Calculate a midpoint with an offset for the curve
    const mid = [
        (source.longitude + target.longitude) / 2,
        (source.latitude + target.latitude) / 2
    ];
    
    // Add some variation to the curve height based on distance
    const distance = Math.sqrt(
        Math.pow(target.longitude - source.longitude, 2) +
        Math.pow(target.latitude - source.latitude, 2)
    );
    
    const curveHeight = distance * 0.2;
    mid[1] += curveHeight;

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
                    'coordinates': [
                        [source.longitude, source.latitude],
                        mid,
                        [target.longitude, target.latitude]
                    ]
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

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the map
    initializeMap();

    const API_ENDPOINT = 'http://localhost:8000';
    
    // Initialize Select2 on Webflow elements
    const vendorSearch = $('.vendor-search-input');
    const clientSearch = $('.client-search-input');
    const vendorResults = $('.vendor-results');
    const clientResults = $('.client-results');
    const vendorStats = $('.vendor-stats-container');
    const clientStats = $('.client-stats-container');
    
    // Configure Select2 for vendor search
    vendorSearch.select2({
        placeholder: 'Search for a vendor...',
        allowClear: true,
        ajax: {
            url: `${API_ENDPOINT}/api/search/vendors`,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term || ''
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(item) {
                        return {
                            id: item,
                            text: item
                        };
                    })
                };
            },
            cache: true
        },
        minimumInputLength: 1
    });

    // Configure Select2 for client search
    clientSearch.select2({
        placeholder: 'Search for a client...',
        allowClear: true,
        ajax: {
            url: `${API_ENDPOINT}/api/search/clients`,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term || ''
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(item) {
                        return {
                            id: item,
                            text: item
                        };
                    })
                };
            },
            cache: true
        },
        minimumInputLength: 1
    });

    // Handle vendor selection
    vendorSearch.on('select2:select', function(e) {
        const vendorName = e.params.data.id;
        // Clear previous results
        vendorResults.empty();
        vendorStats.empty();
        
        // Show and update the header
        $('.vendor-header').show().find('.vendor-name').text(vendorName);
        
        fetch(`${API_ENDPOINT}/api/vendor/${encodeURIComponent(vendorName)}/clients`)
            .then(response => response.json())
            .then(data => {
                displayResults(data.clients, vendorResults);
                displayStats(data.stats, vendorStats);

                // Update map with vendor and clients
                clearMap();
                const vendor = {
                    name: vendorName,
                    domain: data.vendor_domain,
                    latitude: data.vendor_latitude,
                    longitude: data.vendor_longitude
                };
                addCompanyToMap(vendor, true);

                // Add client markers and connections
                data.clients.forEach((client, index) => {
                    if (client.latitude && client.longitude) {
                        addCompanyToMap(client);
                        drawConnection(vendor, client, index);
                    }
                });

                // Update map view
                updateMapView([vendor, ...data.clients]);
            })
            .catch(error => {
                console.error('Error:', error);
                vendorResults.html('<div class="error-message">Failed to fetch clients</div>');
            });ge">Failed to fetch clients</div>');
            });
    });

    // Handle client selection
    clientSearch.on('select2:select', function(e) {
        const clientName = e.params.data.id;
        // Clear previous results
        clientResults.empty();
        clientStats.empty();
        
        // Show and update the header
        $('.client-header').show().find('.client-name').text(clientName);
        
        fetch(`${API_ENDPOINT}/api/client/${encodeURIComponent(clientName)}/vendors`)
            .then(response => response.json())
            .then(data => {
                displayResults(data.vendors, clientResults);
                displayStats(data.stats, clientStats);

                // Update map with client and vendors
                clearMap();
                const client = {
                    name: clientName,
                    domain: data.client_domain,
                    latitude: data.client_latitude,
                    longitude: data.client_longitude
                };
                addCompanyToMap(client, true);

                // Add vendor markers and connections
                data.vendors.forEach((vendor, index) => {
                    if (vendor.latitude && vendor.longitude) {
                        addCompanyToMap(vendor);
                        drawConnection(client, vendor, index);
                    }
                });

                // Update map view
                updateMapView([client, ...data.vendors]);
            })
            .catch(error => {
                console.error('Error:', error);
                clientResults.html('<div class="error-message">Failed to fetch vendors</div>');
            });ge">Failed to fetch vendors</div>');
            });
    });

    function displayResults(companies, container) {
        if (!companies || companies.length === 0) {
            container.html('<div class="no-results">No relationships found.</div>');
            return;
        }

        // Create a simple list of companies
        const list = $('<ul class="company-list"></ul>');
        
        companies.forEach(company => {
            const item = $('<li class="company-item"></li>');
            const name = company.name || 'Unknown Company';
            
            // Create HTML for domain link if domain exists
            let domainHtml = '';
            if (company.domain) {
                const domainUrl = company.domain.startsWith('http') ? company.domain : `https://${company.domain}`;
                domainHtml = ` (<a href="${domainUrl}" target="_blank" class="domain-link">${company.domain}</a>)`;
            }
            
            // Set HTML content instead of text to allow for the link
            item.html(`${name}${domainHtml}`);
            list.append(item);
        });
        
        container.append(list);
    }
    
    function displayStats(stats, container) {
        if (!stats) return;
        
        // Create a clone of your stats template
        const template = $('.stats-template').clone();
        
        // Update stats
        template.find('.total-count').text(stats.total || 0);
        template.find('.with-location').text(stats.with_location || 0);
        template.find('.with-logo').text(stats.with_logo || 0);
        
        // Make template visible and add to container
        template.removeClass('stats-template');
        template.show();
        container.append(template);
    }
});
