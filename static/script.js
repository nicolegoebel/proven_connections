// Initialize map and store globally
let map;
let currentMarkers = [];
let currentConnections = [];

async function initializeMap() {
    try {
        console.log('Fetching map config...');
        const response = await fetch('./api/config/map');
        console.log('Map config response:', response);
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

// No longer needed as we get logos from the API
// Keeping function signature for compatibility
async function getFaviconUrl(domain) {
    return null;
}

async function addCompanyToMap(company, isCenter = false) {
    if (!company.latitude || !company.longitude) return null;

    console.log('Adding company to map:', company);

    // Create marker element with fixed dimensions
    const size = isCenter ? 40 : 32;
    const el = document.createElement('div');
    el.className = 'marker';
    el.style.width = `${size}px`;
    el.style.height = `${size}px`;
    el.style.cursor = company.domain ? 'pointer' : 'default';
    el.style.transition = 'all 0.2s ease-in-out';
    el.style.display = 'flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';
    el.style.borderRadius = '50%';
    el.style.border = `3px solid ${isCenter ? '#2563eb' : '#64748b'}`;
    el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
    el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    el.style.backgroundSize = '75%';
    el.style.backgroundPosition = 'center';
    el.style.backgroundRepeat = 'no-repeat';
    el.style.position = 'absolute';
    el.style.transform = 'translate(-50%, -50%)';


    
    // Use logo from API if available
    if (company.logo) {
        console.log(`Attempting to load logo for ${company.name}:`, company.logo);
        try {
            // Create a promise to handle image loading
            await new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => {
                    console.log(`Logo loaded successfully for ${company.name}`, img.width, 'x', img.height);
                    el.style.backgroundImage = `url(${company.logo})`;
                    el.style.backgroundColor = 'white';
                    resolve();
                };
                img.onerror = (error) => {
                    console.error(`Failed to load logo for ${company.name}:`, error);
                    reject(error);
                };
                img.src = company.logo;
            });
        } catch (error) {
            console.error(`Error loading logo for ${company.name}:`, error);
            // Fallback to default marker style
            el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
        }
    } else {
        console.log(`No logo available for ${company.name}`);
    }
    
    el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';

    // Add custom styles for popups if not already added
    if (!document.getElementById('custom-popup-styles')) {
        const style = document.createElement('style');
        style.id = 'custom-popup-styles';
        style.textContent = `
            .mapboxgl-popup-content {
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .popup-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .popup-logo {
                width: 24px;
                height: 24px;
                object-fit: contain;
                border-radius: 4px;
            }
            .popup-info {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .popup-info h4 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
                color: #1a1a1a;
            }
            .popup-domain {
                font-size: 12px;
                color: #2563eb;
                text-decoration: none;
            }
            .popup-domain:hover {
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }

    // Create popup with offset based on marker size
    const popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: [0, -(size/2 + 8)],
        className: 'custom-popup'
    })
    .setHTML(`
        <div class="popup-content">
            ${company.logo ? `<img src="${company.logo}" alt="${company.name} logo" class="popup-logo" onerror="this.style.display='none'">` : ''}
            <div class="popup-info">
                <h4>${company.name}</h4>
                ${company.domain ? `<a href="https://${company.domain}" target="_blank" class="popup-domain">${company.domain}</a>` : ''}
            </div>
        </div>
    `);

    // Add click handler to open domain in new tab if it exists
    if (company.domain) {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.open(`https://${company.domain}`, '_blank');
        });
    }

    // Create marker
    const marker = new mapboxgl.Marker({
        element: el,
        anchor: 'center'
    })
    .setLngLat([company.longitude, company.latitude])
    .setPopup(popup)
    .addTo(map);

    // Add hover effect styles if not already added
    if (!document.getElementById('marker-hover-styles')) {
        const style = document.createElement('style');
        style.id = 'marker-hover-styles';
        style.textContent = `
            .marker {
                position: relative;
            }
            .marker::before {
                content: '';
                position: absolute;
                inset: -6px;
                border-radius: 50%;
                background: rgba(37, 99, 235, 0.1);
                opacity: 0;
                transition: opacity 0.2s ease;
                pointer-events: none;
                z-index: -1;
            }
            .marker:hover::before {
                opacity: 1;
            }
            .marker {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                background-position: center;
                background-size: 75%;
                background-repeat: no-repeat;
            }
        `;
        document.head.appendChild(style);
    }

    el.addEventListener('mouseenter', () => {
        marker.getPopup().addTo(map);
        if (!company.logo) {
            el.style.backgroundColor = isCenter ? '#1d4ed8' : '#475569';
        }
        el.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
    });
    
    el.addEventListener('mouseleave', () => {
        marker.getPopup().remove();
        if (!company.logo) {
            el.style.backgroundColor = isCenter ? '#2563eb' : '#64748b';
        }
        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
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

async function displayCompanies(data, containerId, type) {
    console.log('Displaying companies:', { data, containerId, type });
    const resultsContainer = $(containerId).empty();
    
    if (!data || !data.center || !data.related || data.related.length === 0) {
        console.log('No data to display:', { data });
        const header = $('<div>').addClass('relationship-header')
            .text(`${data?.center?.name || 'This company'} ${type === 'Clients' ? 'provides no services to clients at the moment' : 'is not a client of any companies at the moment'}`)
            .show();
        resultsContainer.closest('.search-column').find('.relationship-header').replaceWith(header);
        resultsContainer.empty();
        clearMap();
        return;
    }

    console.log('Center company:', data.center);
    console.log('Related companies:', data.related);

    // Clear previous markers and connections
    clearMap();

    const centerCompany = data.center;
    const companies = data.related;

    // Display header with count
    const count = companies.length;
    const isServiceProvider = type === 'Clients';
    
    // Create header with company name
    const headerNameSpan = $('<span>')
        .text(centerCompany.name)
        .css('font-weight', '600');
    
    let headerText;
    if (isServiceProvider) {
        headerText = count === 1
            ? ' provides services to the following client:'
            : count === 0
            ? ' provides no services to clients at the moment'
            : ` provides services to the following ${count} clients:`;
    } else {
        headerText = count === 1
            ? ' is a client of the following company:'
            : count === 0
            ? ' is not a client of any companies at the moment'
            : ` is a client of the following ${count} companies:`;
    }
    
    const header = $('<div>')
        .addClass('relationship-header')
        .css('margin-bottom', '2px')
        .css('display', 'flex')
        .css('align-items', 'center')
        .css('gap', '4px')
        .show()
        .append(
            headerNameSpan,
            $('<span>').text(headerText)
        );
    
    resultsContainer.closest('.search-column').find('.relationship-header').replaceWith(header);

    // Add custom styles for company cards and headers if not already added
    if (!document.getElementById('custom-card-styles')) {
        const style = document.createElement('style');
        style.id = 'custom-card-styles';
        style.textContent = `
            .relationship-header {
                font-size: 14px;
                line-height: 1.4;
                padding-bottom: 12px;
                margin-bottom: 12px !important;
                border-bottom: 1px solid #e5e7eb;
            }
            .relationship-header .company-tag {
                font-size: 7px;
                padding: 0 4px;
                border-radius: 3px;
                text-transform: uppercase;
                letter-spacing: 0.1px;
                line-height: 18px;
                height: 18px;
                display: inline-flex;
                align-items: center;
                white-space: nowrap;
                vertical-align: middle;
            }
            .company-card {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px;
                border-radius: 6px;
                transition: background-color 0.2s;
                height: auto;
                min-height: 32px;
            }
            .company-card .company-tag {
                font-size: 7px;
                padding: 0 4px;
                border-radius: 3px;
                text-transform: uppercase;
                letter-spacing: 0.1px;
                line-height: 18px;
                height: 18px;
                display: flex;
                align-items: center;
                white-space: nowrap;
                margin-right: -2px;
            }
            .service-provider-tag {
                background-color: rgba(37, 99, 235, 0.1);
                color: #2563eb;
                border: 1px solid #2563eb;
            }
            .client-tag {
                background-color: rgba(100, 116, 139, 0.1);
                color: #64748b;
                border: 1px solid #64748b;
            }
            .company-card:hover {
                background-color: #f8fafc;
            }
            .company-logo {
                width: 20px;
                height: 20px;
                border-radius: 3px;
                object-fit: contain;
                background-color: white;
                flex-shrink: 0;
                border: 1px solid #e5e7eb;
            }
            /* Style for card and selection tags */
            .company-card .company-tag,
            .select2-selection-company .company-tag {
                font-size: 8px;
                padding: 1px 3px;
                border-radius: 2px;
                text-transform: uppercase;
                letter-spacing: 0.2px;
                line-height: 1.1;
                height: 12px;
                display: flex;
                align-items: center;
            }
            .select2-selection-company {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 1px 0;
            }
            .select2-selection-logo {
                width: 16px;
                height: 16px;
                object-fit: contain;
                border-radius: 2px;
            }
            .company-info {
                display: flex;
                flex-direction: column;
                gap: 2px;
                flex: 1;
                min-width: 0;
            }
            
            /* Select2 Dropdown Styles */
            .select2-result-company {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px;
                min-height: 32px;
            }
            
            .select2-result-company .company-tag {
                font-size: 7px;
                padding: 0 4px;
                line-height: 18px;
                height: 18px;
                border-radius: 3px;
                margin-right: -2px;
            }
            
            .select2-result-logo {
                width: 20px;
                height: 20px;
                border-radius: 3px;
                object-fit: contain;
                background-color: white;
                border: 1px solid #e5e7eb;
                flex-shrink: 0;
            }
            
            .select2-result-company__name {
                font-size: 14px;
                flex: 1;
                line-height: 20px;

            }
            .company-name {
                font-weight: 500;
                color: #1a1a1a;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .company-domain {
                font-size: 12px;
                color: #2563eb;
                text-decoration: none;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .company-domain:hover {
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }

    // Create cards for each company
    const resultsWrapper = $('<div>').addClass(type.toLowerCase() === 'clients' ? 'vendor-results' : 'client-results');
    companies.forEach(company => {
        const card = $('<div>').addClass('company-card');
        
        // Add type tag
        const isServiceProvider = type === 'Service Providers';
        const tagType = isServiceProvider ? 'service-provider-tag' : 'client-tag';
        const tagText = isServiceProvider ? 'Service Provider' : 'Client';
        const tag = $('<span>')
            .addClass(`company-tag ${tagType}`)
            .text(tagText);
        card.append(tag);

        // Add logo if available
        if (company.logo) {
            const logoImg = $('<img>')
                .addClass('company-logo')
                .attr('src', company.logo)
                .attr('alt', `${company.name} logo`)
                .on('error', function() {
                    $(this).hide();
                });
            card.append(logoImg);
        }

        // Create info container
        const infoContainer = $('<div>').addClass('company-info');
        
        // Add company name
        const nameEl = $('<div>').addClass('company-name').text(company.name);
        infoContainer.append(nameEl);
        
        // Add domain link if available
        if (company.domain) {
            const domainLink = $('<a>')
                .addClass('company-domain')
                .attr('href', `https://${company.domain}`)
                .attr('target', '_blank')
                .text(company.domain);
            infoContainer.append(domainLink);
        }
        
        card.append(infoContainer);
        resultsWrapper.append(card);
    });
    resultsContainer.empty().append(resultsWrapper);

    // Update map
    console.log('Updating map with companies...');
    clearMap();
    console.log('Adding center company marker:', centerCompany);
    const centerMarker = await addCompanyToMap(centerCompany, true);

    // Add company markers and connections
    for (let i = 0; i < companies.length; i++) {
        const company = companies[i];
        console.log(`Adding related company marker ${i + 1}/${companies.length}:`, company);
        const marker = await addCompanyToMap(company);
        if (marker && centerMarker) {
            console.log(`Drawing connection ${i + 1}/${companies.length}`);
            drawConnection(centerCompany, company, i);
        }
    }

    // Update map view
    updateMapView([centerCompany, ...companies]);
}

function displayError(containerId, message) {
    const header = $('<div>')
        .addClass('relationship-header')
        .text(message)
        .show();
    $(containerId)
        .closest('.search-column')
        .find('.relationship-header')
        .replaceWith(header);
    $(containerId).empty();
    clearMap();
}

// Initialize when document is ready
$(document).ready(async function() {
    // Initialize the map
    await initializeMap();


    // Initialize Select2 for unified company search
    $('#company-search').select2({
        placeholder: 'Search for any company...',

        allowClear: true,
        ajax: {
            url: './api/search/companies',
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
                            text: item.name,
                            type: item.type,
                            logo: item.logo,
                            domain: item.domain
                        };
                    })
                };
            },
            cache: true
        },
        minimumInputLength: 1,
        templateResult: formatCompanyResult,
        templateSelection: formatCompanySelection
    });

    // Format the company result in the dropdown
    function formatCompanyResult(company) {
        if (!company.id) return company.text;

        const type = company.type === 'service_provider' ? 'Service Provider' : 'Client';
        const typeClass = company.type === 'service_provider' ? 'service-provider-tag' : 'client-tag';
        
        return $(`
            <div class="select2-result-company">
                <span class="company-tag ${typeClass}">${type}</span>
                ${company.logo ? `<img src="${company.logo}" class="select2-result-logo" onerror="this.style.display='none'">` : ''}
                <span class="select2-result-company__name">${company.text}</span>
            </div>
        `);
    }

    // Format the selected company
    function formatCompanySelection(company) {
        if (!company.id) return company.text;
        return company.text;
    }

    // Handle company selection
    $('#company-search').on('select2:select', async function(e) {
        const companyName = e.params.data.id;
        const companyType = e.params.data.type;
        console.log('Selected company:', companyName, 'Type:', companyType);

        try {
            const endpoint = companyType === 'service_provider' 
                ? `/api/vendor/${encodeURIComponent(companyName)}/clients`
                : `/api/client/${encodeURIComponent(companyName)}/vendors`;

            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Company relationships data:', data);

            if (data && data.center) {
                const relationType = companyType === 'service_provider' ? 'Clients' : 'Service Providers';
                await displayCompanies(data, '#company-results', relationType);
            } else {
                console.log('No relationships found for company:', companyName);
                const message = companyType === 'service_provider'
                    ? 'No client relationships found for this service provider'
                    : 'No service provider relationships found for this client';
                displayError('#company-results', message);
            }
        } catch (error) {
            console.error('Failed to fetch relationships:', error);
            displayError('#company-results', 'Failed to fetch relationship data. Please try again.');
        }
    });

    // Handle clear
    $('#company-search').on('select2:clear', function() {
        $('#company-results').empty();
        clearMap();
    });
});
