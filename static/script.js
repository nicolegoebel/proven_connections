$(document).ready(function() {
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
    });

    $('#client-search').on('select2:clear', function() {
        $('#client-vendors').empty();
    });
});

function fetchVendorClients(vendorName) {
    $.get(`/api/vendor/${encodeURIComponent(vendorName)}/clients`)
        .done(function(clients) {
            displayCompanies(clients, '#vendor-clients', 'Clients');
        })
        .fail(function(jqXHR) {
            displayError('#vendor-clients', 'Failed to fetch clients');
        });
}

function fetchClientVendors(clientName) {
    $.get(`/api/client/${encodeURIComponent(clientName)}/vendors`)
        .done(function(vendors) {
            displayCompanies(vendors, '#client-vendors', 'Vendors');
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
