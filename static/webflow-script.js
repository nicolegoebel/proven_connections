// Webflow-compatible script
document.addEventListener('DOMContentLoaded', function() {
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
