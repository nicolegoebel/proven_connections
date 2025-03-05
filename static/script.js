// Initialize map and store globally
let map;
let currentMarkers = [];
let currentConnections = [];

async function initializeMap() {
    try {
        const response = await fetch('/api/config/map');
        const config = await response.json();
        
        mapboxgl.accessToken = config.accessToken;
        map = new mapboxgl.Map({
            container: 'map',
            style: config.style,
            center: config.center,
            zoom: config.zoom
        });
    } catch (error) {
        console.error('Failed to initialize map:', error);
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
    $('#vendor-search').on('select2:select', function(e) {
        const vendorName = e.params.data.id;
        fetchVendorClients(vendorName);
    });

    // Handle client selection
    $('#client-search').on('select2:select', function(e) {
        const clientName = e.params.data.id;
        fetchClientVendors(clientName);
    });

    // Clear results when selection is cleared
    $('#vendor-search').on('select2:clear', function() {
        $('#vendor-clients').empty();
        clearMap();
    });

    $('#client-search').on('select2:clear', function() {
        $('#client-vendors').empty();
        clearMap();
    });
});

function fetchVendorClients(vendorName) {
    $.get(`/api/vendor/${encodeURIComponent(vendorName)}/clients`)
        .done(function(data) {
            displayCompanies(data.clients, '#vendor-clients', 'Clients');

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
        .fail(function(jqXHR) {
            displayError('#vendor-clients', 'Failed to fetch clients');
        });
}

function fetchClientVendors(clientName) {
    $.get(`/api/client/${encodeURIComponent(clientName)}/vendors`)
        .done(function(data) {
            displayCompanies(data.vendors, '#client-vendors', 'Vendors');

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
        .fail(function(jqXHR) {
            displayError('#client-vendors', 'Failed to fetch vendors');
        });
}

function displayCompanies(companies, containerId, type) {
    const container = $(containerId);
    container.empty();
    
    if (companies.length === 0) {
        container.append(`<div class="alert alert-info">No ${type.toLowerCase()} found.</div>`);
        return;
    }

    companies.forEach(function(company) {
        const card = $(`
            <div class="card company-card">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-auto">
                            ${company.logo ? 
                                `<img src="${company.logo}" alt="${company.name} logo" class="company-logo">` :
                                '<div class="company-logo-placeholder"></div>'
                            }
                        </div>
                        <div class="col">
                            <h5 class="card-title mb-1">${company.name}</h5>
                            <p class="card-text text-muted mb-1">
                                <small>${company.domain || 'No domain available'}</small>
                            </p>
                            ${company.latitude && company.longitude ?
                                `<p class="card-text"><small>Location: ${company.latitude.toFixed(4)}, ${company.longitude.toFixed(4)}</small></p>` :
                                '<p class="card-text"><small>Location: Not available</small></p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `);
        container.append(card);
    });
}

function displayError(containerId, message) {
    const container = $(containerId);
    container.empty().append(`
        <div class="alert alert-danger">
            ${message}
        </div>
    `);
}
